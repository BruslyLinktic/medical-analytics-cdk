#!/usr/bin/env python3
import boto3
import json
import time
import sys

# ID de la distribución CloudFront mostrada en la captura de pantalla
DISTRIBUTION_ID = 'EBPFC2GQEWZC1'

def update_cloudfront_csp():
    """Actualiza la política CSP de CloudFront para permitir scripts y estilos inline."""
    print(f"Actualizando política CSP para distribución CloudFront: {DISTRIBUTION_ID}")
    cloudfront_client = boto3.client('cloudfront')
    
    try:
        # Obtener la configuración actual
        response = cloudfront_client.get_distribution_config(Id=DISTRIBUTION_ID)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        print("Configuración de CloudFront obtenida correctamente")
        
        # Obtener la política de encabezados de respuesta actual
        default_behavior = config.get('DefaultCacheBehavior', {})
        response_headers_policy_id = default_behavior.get('ResponseHeadersPolicyId')
        
        if not response_headers_policy_id:
            print("No se encontró una política de encabezados de respuesta configurada")
            print("Creando una nueva política desde cero...")
            
            # Crear una nueva política de seguridad completa
            new_policy_config = {
                'Name': f'medical-analytics-csp-fixed-{int(time.time())}',
                'Comment': 'Política CSP que permite scripts y estilos inline',
                'CorsConfig': {
                    'AccessControlAllowCredentials': False,
                    'AccessControlAllowHeaders': {
                        'Items': ['*'],
                        'Quantity': 1
                    },
                    'AccessControlAllowMethods': {
                        'Items': ['GET', 'HEAD', 'OPTIONS', 'PUT', 'POST', 'DELETE', 'PATCH'],
                        'Quantity': 7
                    },
                    'AccessControlAllowOrigins': {
                        'Items': ['*'],
                        'Quantity': 1
                    },
                    'AccessControlMaxAgeSec': 600,
                    'OriginOverride': True
                },
                'SecurityHeadersConfig': {
                    'ContentSecurityPolicy': {
                        'ContentSecurityPolicy': "default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;",
                        'Override': True
                    },
                    'StrictTransportSecurity': {
                        'AccessControlMaxAgeSec': 31536000,  # 1 año
                        'IncludeSubdomains': True,
                        'Override': True
                    }
                }
            }
        else:
            # Obtener detalles de la política actual
            try:
                policy_response = cloudfront_client.get_response_headers_policy(Id=response_headers_policy_id)
                policy = policy_response.get('ResponseHeadersPolicy', {})
                policy_config = policy.get('ResponseHeadersPolicyConfig', {})
                
                print(f"Política actual encontrada: {policy_config.get('Name')}")
                
                # Crear una nueva política con CSP actualizado
                new_policy_config = {
                    'Name': policy_config.get('Name') + '-fixed-csp',
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
                        
                        print(f"CSP actual: {csp_value}")
                        
                        # Agregar 'unsafe-inline' a script-src y style-src si no está ya presente
                        if 'script-src' in csp_value and "'unsafe-inline'" not in csp_value:
                            csp_value = csp_value.replace("script-src", "script-src 'unsafe-inline'")
                        
                        if 'style-src' in csp_value and "'unsafe-inline'" not in csp_value:
                            csp_value = csp_value.replace("style-src", "style-src 'unsafe-inline'")
                        
                        new_policy_config['SecurityHeadersConfig']['ContentSecurityPolicy']['ContentSecurityPolicy'] = csp_value
                        
                        print(f"CSP actualizado: {csp_value}")
                    else:
                        # Si no existe ContentSecurityPolicy pero sí SecurityHeadersConfig
                        new_policy_config['SecurityHeadersConfig']['ContentSecurityPolicy'] = {
                            'Override': True,
                            'ContentSecurityPolicy': "default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
                        }
                else:
                    # Si no existe ninguna configuración de seguridad
                    new_policy_config['SecurityHeadersConfig'] = {
                        'ContentSecurityPolicy': {
                            'Override': True,
                            'ContentSecurityPolicy': "default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
                        },
                        'StrictTransportSecurity': {
                            'AccessControlMaxAgeSec': 31536000,  # 1 año
                            'IncludeSubdomains': True,
                            'Override': True
                        }
                    }
            except Exception as e:
                print(f"Error al obtener la política actual: {str(e)}")
                print("Creando una nueva política desde cero...")
                
                # Crear una nueva política de seguridad completa
                new_policy_config = {
                    'Name': f'medical-analytics-csp-fixed-{int(time.time())}',
                    'Comment': 'Política CSP que permite scripts y estilos inline',
                    'SecurityHeadersConfig': {
                        'ContentSecurityPolicy': {
                            'Override': True,
                            'ContentSecurityPolicy': "default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
                        },
                        'StrictTransportSecurity': {
                            'AccessControlMaxAgeSec': 31536000,  # 1 año
                            'IncludeSubdomains': True,
                            'Override': True
                        }
                    }
                }
        
        print("Creando nueva política de encabezados...")
        
        # Crear la nueva política
        create_response = cloudfront_client.create_response_headers_policy(
            ResponseHeadersPolicyConfig=new_policy_config
        )
        
        new_policy_id = create_response['ResponseHeadersPolicy']['Id']
        print(f"Nueva política de encabezados creada con ID: {new_policy_id}")
        
        # Actualizar la distribución para usar la nueva política
        config['DefaultCacheBehavior']['ResponseHeadersPolicyId'] = new_policy_id
        
        print("Actualizando distribución CloudFront...")
        update_response = cloudfront_client.update_distribution(
            Id=DISTRIBUTION_ID,
            IfMatch=etag,
            DistributionConfig=config
        )
        
        print(f"Distribución CloudFront actualizada correctamente")
        print("Los cambios pueden tardar hasta 15 minutos en propagarse completamente")
        
        return True
    
    except Exception as e:
        print(f"Error al actualizar la política CSP de CloudFront: {str(e)}")
        return False

def main():
    print("=== Script de Corrección de CSP para CloudFront ===")
    
    if not update_cloudfront_csp():
        print("No se pudo actualizar la política CSP de CloudFront")
        sys.exit(1)
    
    print("\n=== Correcciones completadas ===")
    print("IMPORTANTE: Los cambios en CloudFront pueden tardar hasta 15 minutos en propagarse completamente.")
    print("Si los problemas persisten después de 15 minutos, limpia la caché de tu navegador o contacta al administrador del sistema.")

if __name__ == "__main__":
    main()
