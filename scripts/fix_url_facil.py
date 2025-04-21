#!/usr/bin/env python3
"""
Script simplificado para arreglar la URL de API y API Key en el frontend.
Este script corrige el error: Failed to parse URL from https://${Token[TOKEN.177]}.execute-api...
"""
import boto3
import re
import sys
import time

# Valores específicos obtenidos de las capturas de pantalla
DISTRIBUTION_ID = 'EBPFC2GQEWZC1'
BUCKET_NAME = 'medical-analytics-frontend-141449707223-us-east-2'

def main():
    print("\n=== Corrección de URL de API en Frontend ===\n")
    
    # Usar el bucket S3 identificado en las imágenes
    bucket_name = BUCKET_NAME
    print(f"Bucket S3: {bucket_name}")
    
    # Pedir la URL del API Gateway
    print("\nPor favor, ingresa la URL del API Gateway")
    print("Ejemplo: https://xyz123abc.execute-api.us-east-2.amazonaws.com/dev/")
    api_url = input("> ").strip()
    
    if not api_url:
        print("Error: No se ingresó una URL")
        return
    
    # Agregar / al final si no lo tiene
    if not api_url.endswith('/'):
        api_url += '/'
    
    # Pedir la API Key
    print("\nPor favor, ingresa la API Key")
    print("Puedes encontrarla en la consola de API Gateway > API Keys")
    api_key = input("> ").strip()
    
    if not api_key:
        print("Error: No se ingresó una API Key")
        return
    
    # Descargar el archivo index.html
    print("\nDescargando index.html...")
    s3 = boto3.client('s3')
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key='index.html')
        html_content = response['Body'].read().decode('utf-8')
        print("✓ Archivo descargado correctamente")
    except Exception as e:
        print(f"✗ Error al descargar el archivo: {str(e)}")
        return
    
    # Reemplazar los tokens no resueltos
    print("\nReemplazando tokens no resueltos...")
    modified_content = html_content
    
    # Reemplazar token de URL API en patrones específicos
    api_endpoint = f"{api_url}upload"
    
    # Patrón del error que viste: ${Token[TOKEN.177]}.execute-api.us-east-...
    token_api_pattern = r'https://\$\{Token\[TOKEN\.\d+\]\}\.execute-api\.[^\'"]+'
    if re.search(token_api_pattern, modified_content):
        modified_content = re.sub(token_api_pattern, api_endpoint, modified_content)
        print("✓ Tokens de URL API reemplazados")
    
    # Reemplazar token de API Key
    token_key_pattern = r'[\'"]\s*x-api-key[\'"]:\s*[\'"](\$\{Token\[TOKEN\.\d+\]\}|{{API_KEY}})[\'"]'
    if re.search(token_key_pattern, modified_content):
        modified_content = re.sub(token_key_pattern, f'"x-api-key":"{api_key}"', modified_content)
        print("✓ Tokens de API Key reemplazados")
    
    # Reemplazar placeholders
    if "{{API_ENDPOINT}}" in modified_content:
        modified_content = modified_content.replace("{{API_ENDPOINT}}", api_endpoint)
        print("✓ Placeholder {{API_ENDPOINT}} reemplazado")
    
    if "{{API_KEY}}" in modified_content:
        modified_content = modified_content.replace("{{API_KEY}}", api_key)
        print("✓ Placeholder {{API_KEY}} reemplazado")
    
    # Guardar el archivo actualizado
    print("\nGuardando cambios...")
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key='index.html',
            Body=modified_content,
            ContentType='text/html'
        )
        print("✓ Archivo actualizado correctamente")
    except Exception as e:
        print(f"✗ Error al guardar el archivo: {str(e)}")
        return
    
    # Invalidar la caché de CloudFront
    print("\nInvalidando caché de CloudFront...")
    cloudfront = boto3.client('cloudfront')
    
    try:
        response = cloudfront.create_invalidation(
            DistributionId=DISTRIBUTION_ID,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/index.html']
                },
                'CallerReference': f'fix-api-url-{int(time.time())}'
            }
        )
        invalidation_id = response['Invalidation']['Id']
        print(f"✓ Caché invalidada correctamente (ID: {invalidation_id})")
    except Exception as e:
        print(f"⚠ Error al invalidar caché: {str(e)}")
        print("  Los cambios se aplicarán cuando expire la caché (hasta 24 horas)")
    
    print("\n=== Proceso completado ===")
    print(f"Ahora puedes acceder a tu aplicación en: https://d2fypua5bbhj7a.cloudfront.net/")
    print("IMPORTANTE:")
    print("1. Los cambios pueden tardar unos minutos en propagarse")
    print("2. Limpia la caché de tu navegador (Ctrl+F5 o Cmd+Shift+R)")
    print("3. Si continúas viendo errores, intenta abrir la página en una ventana de incógnito")

if __name__ == "__main__":
    main()
