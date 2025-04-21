#!/usr/bin/env python3
import boto3
import json
import sys

# ID de la distribución CloudFront mostrada en la captura de pantalla
DISTRIBUTION_ID = 'EBPFC2GQEWZC1'
KMS_ALIAS = 'medical-analytics-key'  # El alias que se utiliza en el código

def get_kms_key_id(alias_name):
    """Obtiene el ID de la clave KMS por su alias."""
    print(f"Buscando clave KMS con alias: {alias_name}")
    kms_client = boto3.client('kms')
    
    try:
        response = kms_client.describe_key(KeyId=f'alias/{alias_name}')
        key_id = response['KeyMetadata']['KeyId']
        print(f"Clave KMS encontrada con ID: {key_id}")
        return key_id
    except Exception as e:
        print(f"Error al obtener la clave KMS con alias {alias_name}: {str(e)}")
        
        # Intentar listar todas las claves como alternativa
        try:
            print("Listando todas las claves KMS disponibles...")
            response = kms_client.list_keys()
            for key in response['Keys']:
                try:
                    key_info = kms_client.describe_key(KeyId=key['KeyId'])
                    key_desc = key_info['KeyMetadata'].get('Description', '')
                    if 'medical' in key_desc.lower() or 'analytics' in key_desc.lower():
                        print(f"Encontrada posible clave por descripción: {key['KeyId']} - {key_desc}")
                        return key['KeyId']
                except Exception:
                    pass
        except Exception as list_error:
            print(f"Error al listar claves KMS: {str(list_error)}")
        
        return None

def update_kms_policy(key_id):
    """Actualiza la política de la clave KMS para permitir acceso desde CloudFront."""
    print(f"Actualizando política para clave KMS: {key_id}")
    kms_client = boto3.client('kms')
    sts_client = boto3.client('sts')
    
    # Obtener el ID de cuenta actual
    account_id = sts_client.get_caller_identity()["Account"]
    
    # Construir el ARN de la distribución CloudFront
    cloudfront_dist_arn = f"arn:aws:cloudfront::{account_id}:distribution/{DISTRIBUTION_ID}"
    
    try:
        # Obtener la política actual
        response = kms_client.get_key_policy(KeyId=key_id, PolicyName='default')
        current_policy = json.loads(response['Policy'])
        
        print("Política KMS actual:")
        print(json.dumps(current_policy, indent=2))
        
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
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": cloudfront_dist_arn
                }
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
        
        print("Política KMS actualizada:")
        print(json.dumps(current_policy, indent=2))
        
        print(f"Política KMS actualizada exitosamente para la clave {key_id}")
        return True
    
    except Exception as e:
        print(f"Error al actualizar la política de la clave KMS: {str(e)}")
        
        # Intentar crear una política desde cero
        try:
            print("Intentando crear una nueva política...")
            
            basic_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "Enable IAM User Permissions",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{account_id}:root"
                        },
                        "Action": "kms:*",
                        "Resource": "*"
                    },
                    {
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
                        "Resource": "*",
                        "Condition": {
                            "StringEquals": {
                                "AWS:SourceArn": cloudfront_dist_arn
                            }
                        }
                    }
                ]
            }
            
            kms_client.put_key_policy(
                KeyId=key_id,
                PolicyName='default',
                Policy=json.dumps(basic_policy)
            )
            
            print("Nueva política KMS creada exitosamente")
            return True
            
        except Exception as new_policy_error:
            print(f"Error al crear nueva política: {str(new_policy_error)}")
            return False

def main():
    print("=== Script de Corrección de Políticas KMS ===")
    
    # Obtener ID de clave
    key_id = get_kms_key_id(KMS_ALIAS)
    if not key_id:
        print(f"No se pudo encontrar la clave KMS con el alias {KMS_ALIAS}")
        print("Por favor, proporciona el ID de la clave KMS manualmente")
        key_id = input("ID de clave KMS: ").strip()
        if not key_id:
            print("No se proporcionó un ID de clave válido")
            sys.exit(1)
    
    # Actualizar política KMS
    if not update_kms_policy(key_id):
        print("No se pudo actualizar la política de la clave KMS")
        sys.exit(1)
    
    print("\n=== Correcciones completadas ===")
    print("La política de KMS ha sido actualizada para permitir el acceso desde CloudFront.")

if __name__ == "__main__":
    main()
