#!/usr/bin/env python3
"""
Script para corregir permisos entre CloudFront y S3.
Este script actualiza la política del bucket de frontend para permitir
explícitamente el acceso desde la distribución CloudFront.
"""

import boto3
import json
import argparse
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cloudfront_distribution_info():
    """Obtiene la información de la distribución CloudFront."""
    cf_client = boto3.client('cloudfront')
    
    # Listar todas las distribuciones
    response = cf_client.list_distributions()
    
    distributions = []
    if 'Items' in response['DistributionList']:
        for dist in response['DistributionList']['Items']:
            # Filtrar solo las distribuciones relacionadas con nuestro proyecto
            if 'medical-analytics' in dist['Comment'].lower():
                distributions.append({
                    'Id': dist['Id'],
                    'DomainName': dist['DomainName'],
                    'ARN': dist['ARN'],
                    'Comment': dist['Comment'],
                    'Status': dist['Status'],
                    'Origins': dist['Origins']['Items']
                })
    
    return distributions

def get_frontend_bucket_from_origins(origins):
    """Extrae el nombre del bucket S3 de los orígenes de CloudFront."""
    for origin in origins:
        if 'S3OriginConfig' in origin:
            # Obtener el dominio y separar para obtener el nombre del bucket
            domain = origin['DomainName']
            
            # Para S3 websites, el dominio sigue el patrón bucket-name.s3-website-region.amazonaws.com
            # Para S3 REST API, el dominio sigue el patrón bucket-name.s3.amazonaws.com
            if domain.startswith('medical-analytics-frontend'):
                if '.s3-website-' in domain:
                    return domain.split('.s3-website-')[0]
                elif '.s3.' in domain:
                    return domain.split('.s3.')[0]
    
    return None

def get_oai_from_origins(origins):
    """Extrae el OAI de los orígenes de CloudFront."""
    for origin in origins:
        if 'S3OriginConfig' in origin and 'OriginAccessIdentity' in origin['S3OriginConfig']:
            oai_path = origin['S3OriginConfig']['OriginAccessIdentity']
            # El formato es "origin-access-identity/cloudfront/OAI_ID"
            return oai_path.split('/')[-1]
    
    return None

def get_oai_s3_canonical_id(oai_id):
    """Obtiene el ID canónico de S3 para el OAI."""
    cf_client = boto3.client('cloudfront')
    
    try:
        response = cf_client.get_cloud_front_origin_access_identity(
            Id=oai_id
        )
        return response['CloudFrontOriginAccessIdentity']['S3CanonicalUserId']
    except Exception as e:
        logger.error(f"Error al obtener el ID canónico del OAI: {e}")
        return None

def update_bucket_policy(bucket_name, oai_canonical_id):
    """Actualiza la política del bucket para permitir acceso desde CloudFront."""
    s3_client = boto3.client('s3')
    
    # Primero intentamos obtener la política actual
    try:
        response = s3_client.get_bucket_policy(Bucket=bucket_name)
        current_policy = json.loads(response['Policy'])
    except s3_client.exceptions.NoSuchBucketPolicy:
        # Si no hay política, creamos una nueva
        current_policy = {
            "Version": "2012-10-17",
            "Statement": []
        }
    except Exception as e:
        logger.error(f"Error al obtener la política del bucket: {e}")
        return False
    
    # Crear nueva declaración de política
    cloudfront_statement = {
        "Sid": "AllowCloudFrontServicePrincipal",
        "Effect": "Allow",
        "Principal": {
            "CanonicalUser": oai_canonical_id
        },
        "Action": "s3:GetObject",
        "Resource": f"arn:aws:s3:::{bucket_name}/*"
    }
    
    # Verificar si ya existe una declaración similar
    statement_exists = False
    for statement in current_policy.get("Statement", []):
        # Simplificación: si ya hay un statement para el mismo OAI, lo actualizamos
        if statement.get("Sid") == "AllowCloudFrontServicePrincipal":
            statement_exists = True
            statement["Principal"]["CanonicalUser"] = oai_canonical_id
            statement["Resource"] = f"arn:aws:s3:::{bucket_name}/*"
            break
    
    # Si no existe, agregamos la nueva declaración
    if not statement_exists:
        current_policy.setdefault("Statement", []).append(cloudfront_statement)
    
    # Aplicar la política actualizada
    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(current_policy)
        )
        logger.info(f"Política de bucket actualizada exitosamente para: {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar la política del bucket: {e}")
        return False

def fix_cors_configuration(bucket_name):
    """Configura CORS para el bucket."""
    s3_client = boto3.client('s3')
    
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': [],
                'MaxAgeSeconds': 3000
            }
        ]
    }
    
    try:
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        logger.info(f"Configuración CORS actualizada exitosamente para: {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar la configuración CORS: {e}")
        return False

def fix_cloudfront_permissions():
    """Función principal para corregir los permisos."""
    
    # 1. Obtener información de la distribución CloudFront
    distributions = get_cloudfront_distribution_info()
    
    if not distributions:
        logger.error("No se encontraron distribuciones de CloudFront para el proyecto medical-analytics.")
        return False
    
    # Para cada distribución encontrada
    for dist in distributions:
        logger.info(f"Procesando distribución: {dist['Id']} ({dist['Comment']})")
        
        # 2. Obtener el bucket de frontend desde los orígenes
        bucket_name = get_frontend_bucket_from_origins(dist['Origins'])
        if not bucket_name:
            logger.warning(f"No se pudo determinar el bucket de frontend para la distribución: {dist['Id']}")
            continue
        
        # 3. Obtener el OAI desde los orígenes
        oai_id = get_oai_from_origins(dist['Origins'])
        if not oai_id:
            logger.warning(f"No se encontró un OAI para la distribución: {dist['Id']}")
            continue
        
        # 4. Obtener el ID canónico del OAI
        oai_canonical_id = get_oai_s3_canonical_id(oai_id)
        if not oai_canonical_id:
            logger.warning(f"No se pudo obtener el ID canónico para el OAI: {oai_id}")
            continue
        
        # 5. Actualizar la política del bucket
        if update_bucket_policy(bucket_name, oai_canonical_id):
            logger.info(f"Permisos actualizados exitosamente entre CloudFront y el bucket: {bucket_name}")
        else:
            logger.error(f"Fallo al actualizar los permisos para el bucket: {bucket_name}")
        
        # 6. Configurar CORS para el bucket
        if fix_cors_configuration(bucket_name):
            logger.info(f"Configuración CORS actualizada para el bucket: {bucket_name}")
        else:
            logger.error(f"Fallo al actualizar la configuración CORS para el bucket: {bucket_name}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Corrige los permisos entre CloudFront y S3')
    args = parser.parse_args()
    
    if fix_cloudfront_permissions():
        logger.info("Proceso completado exitosamente.")
    else:
        logger.error("El proceso falló. Revisa los logs para más detalles.")
