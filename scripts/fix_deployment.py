#!/usr/bin/env python3
import boto3
import json
import time
import argparse
import sys

def get_kms_key_id(alias_name):
    """Obtiene el ID de la clave KMS por su alias."""
    kms_client = boto3.client('kms')
    try:
        response = kms_client.describe_key(KeyId=f'alias/{alias_name}')
        return response['KeyMetadata']['KeyId']
    except Exception as e:
        print(f"Error al obtener la clave KMS con alias {alias_name}: {str(e)}")
        return None

def update_kms_policy(key_id, cloudfront_distribution_arn=None):
    """Actualiza la política de la clave KMS para permitir acceso desde CloudFront."""
    kms_client = boto3.client('kms')
    sts_client = boto3.client('sts')
    
    # Obtener el ID de cuenta actual
    account_id = sts_client.get_caller_identity()["Account"]
    
    try:
        # Obtener la política actual
        response = kms_client.get_key_policy(KeyId=key_id, PolicyName='default')
        current_policy = json.loads(response['Policy'])
        
        # Verificar si ya existe una declaración para CloudFront
        cloudfront_statement_exists = False
        for statement in current_policy.get("Statement", []):
            if statement.get("Sid") == "AllowCloudFrontServiceAccess":
                cloudfront_statement_exists = True
                print("Ya existe una política para CloudFront. Actualizando...")
                break
        
        # Crear o actualizar la declaración para CloudFront
        cloudfront_statement = {
            "Sid": "AllowCloudFrontServiceAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": [
                "kms:Decrypt",
                "kms:Encrypt",
                "kms:GenerateDataKey"
            ],
            "Resource": "*"
        }
        
        # Si se proporciona un ARN específico de distribución de CloudFront
        if cloudfront_distribution_arn:
            cloudfront_statement["Condition"] = {
                "StringEquals": {
                    "AWS:SourceArn": cloudfront_distribution_arn
                }
            }
        
        # Actualizar la política
        if cloudfront_statement_exists:
            for i, statement in enumerate(current_policy["Statement"]):
                if statement.get("Sid") == "AllowCloudFrontServiceAccess":
                    current_policy["Statement"][i] = cloudfront_statement
        else:
            current_policy["Statement"].append(cloudfront_statement)
        
        # Guardar la política actualizada
        kms_client.put_key_policy(
            KeyId=key_id,
            PolicyName='default',
            Policy=json.dumps(current_policy)
        )
        
        print(f"Política KMS actualizada exitosamente para la clave {key_id}")
        return True
    
    except Exception as e:
        print(f"Error al actualizar la política de la clave KMS: {str(e)}")
        return False

def get_cloudfront_distribution():
    """Obtiene el ID y ARN de la distribución de CloudFront del proyecto."""
    cloudfront_client = boto3.client('cloudfront')
    sts_client = boto3.client('sts')
    
    # Obtener el ID de cuenta
    account_id = sts_client.get_caller_identity()["Account"]
    
    # ID específico de CloudFront que vemos en la captura de pantalla
    specific_dist_id = 'EBPFC2GQEWZC1'
    
    try:
        # Primero intentamos con el ID específico
        try:
            response = cloudfront_client.get_distribution(Id=specific_dist_id)
            dist_id = specific_dist_id
            region = 'us-east-1'  # CloudFront siempre está en esta región
            dist_arn = f"arn:aws:cloudfront::{account_id}:distribution/{dist_id}"
            print(f"Encontrada distribución CloudFront con ID específico: {dist_id}, ARN: {dist_arn}")
            return dist_id, dist_arn
        except Exception as e:
            print(f"No se pudo encontrar la distribución con ID específico: {specific_dist_id}. Error: {str(e)}")
            print("Buscando entre todas las distribuciones...")
        
        # Si no funciona, buscamos entre todas las distribuciones
        response = cloudfront_client.list_distributions()
        distributions = response.get('DistributionList', {}).get('Items', [])
        
        # Buscar la distribución relacionada con el proyecto
        for dist in distributions:
            # Intentamos buscar por varios criterios
            comment = dist.get('Comment', '').lower()
            domain_name = dist.get('DomainName', '').lower()
            origins = dist.get('Origins', {}).get('Items', [])
            origin_domains = [origin.get('DomainName', '').lower() for origin in origins]
            
            if ('medical' in comment 
                    or 'd2fypua5bbhj7a.cloudfront.net' in domain_name 
                    or 'analytics' in comment
                    or any('d2fypua5bbhj7a' in domain for domain in origin_domains)
                    or dist['Id'] == 'EBPFC2GQEWZC1'):
                dist_id = dist['Id']
                region = 'us-east-1'  # CloudFront siempre está en esta región
                dist_arn = f"arn:aws:cloudfront::{account_id}:distribution/{dist_id}"
                print(f"Encontrada distribución CloudFront: {dist_id}, ARN: {dist_arn}")
                return dist_id, dist_arn
        
        print("No se encontró una distribución de CloudFront para el proyecto")
        return None, None
    
    except Exception as e:
        print(f"Error al listar distribuciones de CloudFront: {str(e)}")
        return None, None

def update_cloudfront_csp(dist_id):
    """Actualiza la política CSP de CloudFront para permitir scripts y estilos inline."""
    cloudfront_client = boto3.client('cloudfront')
    
    try:
        # Obtener la configuración actual
        response = cloudfront_client.get_distribution_config(Id=dist_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Obtener la política de encabezados de respuesta actual
        default_behavior = config.get('DefaultCacheBehavior', {})
        response_headers_policy_id = default_behavior.get('ResponseHeadersPolicyId')
        
        if not response_headers_policy_id:
            print("No se encontró una política de encabezados de respuesta configurada")
            return False
        
        # Obtener detalles de la política actual
        policy_response = cloudfront_client.get_response_headers_policy(Id=response_headers_policy_id)
        policy = policy_response.get('ResponseHeadersPolicy', {})
        policy_config = policy.get('ResponseHeadersPolicyConfig', {})
        
        # Crear una nueva política con CSP actualizado
        new_policy_config = {
            'Name': policy_config.get('Name') + '-fixed',
            'Comment': (policy_config.get('Comment', '') + ' - Updated to allow inline scripts and styles').strip()
        }
        
        # Copiar configuración CORS si existe
        if 'CorsConfig' in policy_config:
            new_policy_config['CorsConfig'] = policy_config['CorsConfig']
        
        # Copiar configuración de seguridad
        if 'SecurityHeadersConfig' in policy_config:
            new_policy_config['SecurityHeadersConfig'] = policy_config['SecurityHeadersConfig'].copy()
            
            # Actualizar CSP si existe
            if 'ContentSecurityPolicy' in new_policy_config['SecurityHeadersConfig']:
                csp = new_policy_config['SecurityHeadersConfig']['ContentSecurityPolicy'].copy()
                csp_value = csp['ContentSecurityPolicy']
                
                # Agregar 'unsafe-inline' a script-src y style-src si no está ya presente
                if 'script-src' in csp_value and "'unsafe-inline'" not in csp_value:
                    csp_value = csp_value.replace("script-src", "script-src 'unsafe-inline'")
                
                if 'style-src' in csp_value and "'unsafe-inline'" not in csp_value:
                    csp_value = csp_value.replace("style-src", "style-src 'unsafe-inline'")
                
                new_policy_config['SecurityHeadersConfig']['ContentSecurityPolicy']['ContentSecurityPolicy'] = csp_value
        else:
            # Si no existe, crear una configuración de seguridad con CSP
            new_policy_config['SecurityHeadersConfig'] = {
                'ContentSecurityPolicy': {
                    'Override': True,
                    'ContentSecurityPolicy': "default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
                }
            }
        
        # Crear la nueva política
        create_response = cloudfront_client.create_response_headers_policy(
            ResponseHeadersPolicyConfig=new_policy_config
        )
        
        new_policy_id = create_response['ResponseHeadersPolicy']['Id']
        print(f"Creada nueva política de encabezados con ID: {new_policy_id}")
        
        # Actualizar la distribución para usar la nueva política
        config['DefaultCacheBehavior']['ResponseHeadersPolicyId'] = new_policy_id
        
        update_response = cloudfront_client.update_distribution(
            Id=dist_id,
            IfMatch=etag,
            DistributionConfig=config
        )
        
        print(f"Distribución CloudFront actualizada con la nueva política CSP")
        print("Los cambios pueden tardar hasta 15 minutos en propagarse completamente")
        
        return True
    
    except Exception as e:
        print(f"Error al actualizar la política CSP de CloudFront: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Corrige problemas de KMS y CSP en la implementación de Medical Analytics")
    parser.add_argument('--skip-kms', action='store_true', help='Omitir la corrección de la política KMS')
    parser.add_argument('--skip-csp', action='store_true', help='Omitir la corrección de la política CSP de CloudFront')
    parser.add_argument('--key-alias', default='medical-analytics-key', help='Alias de la clave KMS (por defecto: medical-analytics-key)')
    args = parser.parse_args()
    
    print("=== Script de Corrección de Medical Analytics ===")
    
    # Obtener información de CloudFront
    dist_id, dist_arn = get_cloudfront_distribution()
    if not dist_id:
        print("No se pudo encontrar la distribución de CloudFront. Asegúrate de que el despliegue se haya completado.")
        if not args.skip_csp:
            return
    
    # Actualizar la política KMS
    if not args.skip_kms:
        print("\n== Actualizando política de KMS ==")
        key_id = get_kms_key_id(args.key_alias)
        if not key_id:
            print(f"No se pudo encontrar la clave KMS con el alias {args.key_alias}")
            print("Verifique que la clave existe y está accesible con sus credenciales actuales")
            return
        
        if not update_kms_policy(key_id, dist_arn):
            print("No se pudo actualizar la política de la clave KMS")
            return
    
    # Actualizar la política CSP de CloudFront
    if not args.skip_csp and dist_id:
        print("\n== Actualizando política CSP de CloudFront ==")
        if not update_cloudfront_csp(dist_id):
            print("No se pudo actualizar la política CSP de CloudFront")
            return
    
    print("\n=== Correcciones completadas ===")
    print("IMPORTANTE: Los cambios en CloudFront pueden tardar hasta 15 minutos en propagarse completamente.")
    print("Si los problemas persisten después de 15 minutos, contacta al administrador del sistema.")

if __name__ == "__main__":
    main()
