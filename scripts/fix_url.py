#!/usr/bin/env python3
"""
Script simplificado para arreglar la URL de API y API Key en el frontend.
Este script corrige el error: Failed to parse URL from https://${Token[TOKEN.177]}.execute-api...
"""
import boto3
import re
import sys

# Valores específicos del proyecto obtenidos de AWS
DISTRIBUTION_ID = 'EBPFC2GQEWZC1'
BUCKET_NAME = 'medical-analytics-frontend-141449707223-us-east-2'

def main():
    print("=== Corrigiendo URLs en frontend ===")
    
    # Usar directamente el bucket que hemos identificado en las imágenes
    bucket_name = BUCKET_NAME
    print(f"Usando bucket S3: {bucket_name}")
    
    # 2. Pedir URL de API Gateway
    print("\nIngresa la URL del API Gateway (ejemplo: https://abc123.execute-api.us-east-2.amazonaws.com/dev/):")
    api_url = input().strip()
    if not api_url:
        print("No se ingresó una URL válida")
        return
    
    # Asegurar que termina con /
    if not api_url.endswith('/'):
        api_url += '/'
    
    # 3. Pedir API Key
    print("\nIngresa la API Key:")
    api_key = input().strip()
    if not api_key:
        print("No se ingresó una API Key válida")
        return
    
    # 4. Descargar index.html
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key='index.html')
        html_content = response['Body'].read().decode('utf-8')
        print("Archivo index.html descargado")
    except Exception as e:
        print(f"Error al descargar index.html: {e}")
        return
    
    # 5. Sustituir tokens y placeholders
    modified_content = html_content
    
    # Sustituir token de URL API
    token_api_pattern = r'https://\$\{Token\[TOKEN\.\d+\]\}\.execute-api\.[^\'"]+'
    if re.search(token_api_pattern, modified_content):
        api_endpoint = f"{api_url}upload"
        modified_content = re.sub(token_api_pattern, api_endpoint, modified_content)
        print("Tokens de URL API reemplazados")
    
    # Sustituir token de API Key
    token_key_pattern = r'[\'"]\$\{Token\[TOKEN\.\d+\]\}[\'"]'
    if re.search(token_key_pattern, modified_content):
        modified_content = re.sub(token_key_pattern, f'"{api_key}"', modified_content)
        print("Tokens de API Key reemplazados")
    
    # Sustituir placeholders
    modified_content = modified_content.replace("{{API_ENDPOINT}}", f"{api_url}upload")
    modified_content = modified_content.replace("{{API_KEY}}", api_key)
    
    # 6. Guardar cambios
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key='index.html',
            Body=modified_content,
            ContentType='text/html'
        )
        print("Archivo index.html actualizado correctamente")
    except Exception as e:
        print(f"Error al guardar index.html: {e}")
        return
    
    # 7. Invalidar caché CloudFront
    try:
        import time
        cloudfront.create_invalidation(
            DistributionId=DISTRIBUTION_ID,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/index.html']
                },
                'CallerReference': f'fix-url-{int(time.time())}'
            }
        )
        print("Caché de CloudFront invalidada")
    except Exception as e:
        print(f"Error al invalidar caché (esto no es crítico): {e}")
    
    print("\n¡Correcciones completadas!")
    print(f"Accede a la aplicación en: https://{DISTRIBUTION_ID}.cloudfront.net/ o d2fypua5bbhj7a.cloudfront.net")
    print("NOTA: Espera unos minutos y limpia la caché de tu navegador si es necesario.")

if __name__ == "__main__":
    main()
