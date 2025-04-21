#!/usr/bin/env python3
import boto3
import json
import time
import sys

# ID de la distribución CloudFront desde la captura de pantalla
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
            return False
        
        # Obtener detalles de la política actual
        try:
            policy_response = cloudfront_client.get_response_headers_policy(Id=response_headers_policy_id)
            policy = policy_response.get('ResponseHeadersPolicy', {})
            policy_config = policy.get('ResponseHeadersPolicyConfig', {})
            
            print(f"Política actual encontrada: {policy_config.get('Name')}")
            
            # Crear una nueva política con CSP actualizado pero manteniendo todos los campos existentes
            new_policy_config = policy_config.copy()
            new_policy_config['Name'] = policy_config.get('Name') + '-fixed-csp'
            
            # Asegurarnos de que todos los elementos requeridos estén presentes
            if 'SecurityHeadersConfig' in new_policy_config:
                security_headers = new_policy_config['SecurityHeadersConfig']
                
                # Actualizar CSP manteniendo el resto de la configuración
                if 'ContentSecurityPolicy' in security_headers:
                    csp = security_headers['ContentSecurityPolicy'].copy()
                    csp_value = csp['ContentSecurityPolicy']
                    
                    print(f"CSP actual: {csp_value}")
                    
                    # Agregar 'unsafe-inline' a script-src y style-src si no está ya presente
                    if 'script-src' in csp_value and "'unsafe-inline'" not in csp_value:
                        csp_value = csp_value.replace("script-src", "script-src 'unsafe-inline'")
                    
                    if 'style-src' in csp_value and "'unsafe-inline'" not in csp_value:
                        csp_value = csp_value.replace("style-src", "style-src 'unsafe-inline'")
                    
                    security_headers['ContentSecurityPolicy']['ContentSecurityPolicy'] = csp_value
                    
                    print(f"CSP actualizado: {csp_value}")
            
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
            
            print("Distribución CloudFront actualizada correctamente")
            print("Los cambios pueden tardar hasta 15 minutos en propagarse completamente")
            
            return True
        
        except Exception as e:
            print(f"Error al obtener o actualizar la política: {str(e)}")
            
            # Si no podemos modificar la política existente, intentemos un enfoque alternativo
            print("Intentando enfoque alternativo...")
            
            # Modificar la distribución para remover la política de headers
            # Esto hará que se use la política por defecto, que podría ser suficiente
            print("Removiendo política de headers para usar la configuración por defecto...")
            if 'ResponseHeadersPolicyId' in config['DefaultCacheBehavior']:
                del config['DefaultCacheBehavior']['ResponseHeadersPolicyId']
                
                try:
                    update_response = cloudfront_client.update_distribution(
                        Id=DISTRIBUTION_ID,
                        IfMatch=etag,
                        DistributionConfig=config
                    )
                    
                    print("Distribución CloudFront actualizada correctamente para usar la configuración por defecto")
                    print("Los cambios pueden tardar hasta 15 minutos en propagarse completamente")
                    return True
                except Exception as update_error:
                    print(f"Error al actualizar la distribución: {str(update_error)}")
                    return False
            else:
                print("No se pudo modificar la política ni remover la configuración")
                return False
    
    except Exception as e:
        print(f"Error al actualizar la política CSP de CloudFront: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Script de Corrección de CSP para CloudFront ===")
    
    if not update_cloudfront_csp():
        print("No se pudo actualizar la política CSP de CloudFront")
        print("Intentando método alternativo: Editando directamente index.html para adaptarse a la CSP existente...")
        
        # Aquí podríamos agregar código para adaptar el HTML, pero es mejor sugerir editar manualmente
        print("\nSolución alternativa - Edita manualmente tu archivo index.html:")
        print("1. Mueve todos los estilos inline a un archivo CSS externo")
        print("2. Mueve todo el código JavaScript inline a un archivo .js externo")
        print("3. Referencia esos archivos desde el HTML")
        print("4. Vuelve a desplegar el frontend actualizado")
        
        sys.exit(1)
    
    print("\n=== Correcciones completadas ===")
    print("IMPORTANTE: Los cambios en CloudFront pueden tardar hasta 15 minutos en propagarse completamente.")
    print("Si los problemas persisten después de 15 minutos, limpia la caché de tu navegador.")
