#!/usr/bin/env python3
import boto3
import json
import sys
import re
import time

# ID de la distribución CloudFront desde la captura de pantalla
DISTRIBUTION_ID = 'EBPFC2GQEWZC1'

def find_frontend_bucket():
    """Identifica el bucket S3 que está usando CloudFront como origen."""
    print("Buscando bucket S3 origen para CloudFront...")
    cloudfront_client = boto3.client('cloudfront')
    s3_client = boto3.client('s3')
    
    try:
        # Obtener la distribución CloudFront
        response = cloudfront_client.get_distribution(Id=DISTRIBUTION_ID)
        distribution = response.get('Distribution', {})
        
        # Obtener la configuración de la distribución
        config = distribution.get('DistributionConfig', {})
        
        # Obtener el origen de la distribución
        origins = config.get('Origins', {}).get('Items', [])
        
        s3_origin_bucket = None
        
        # Buscar el origen S3
        for origin in origins:
            if 's3.amazonaws.com' in origin.get('DomainName', ''):
                origin_domain = origin.get('DomainName', '')
                # Extraer el nombre del bucket del dominio
                s3_origin_bucket = origin_domain.split('.s3.amazonaws.com')[0]
                print(f"Bucket S3 encontrado como origen: {s3_origin_bucket}")
                break
        
        if not s3_origin_bucket:
            # Intenta listar todos los buckets y buscar uno relacionado con el proyecto
            response = s3_client.list_buckets()
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                if 'medical' in bucket_name.lower() or 'analytics' in bucket_name.lower() or 'frontend' in bucket_name.lower():
                    s3_origin_bucket = bucket_name
                    print(f"Bucket S3 encontrado por nombre: {s3_origin_bucket}")
                    break
        
        return s3_origin_bucket
    
    except Exception as e:
        print(f"Error al buscar bucket S3: {str(e)}")
        return None

def get_api_gateway_url():
    """Obtiene la URL del API Gateway del stack de CloudFormation."""
    print("Buscando URL de API Gateway...")
    cfn_client = boto3.client('cloudformation')
    
    try:
        # Buscar el stack de ingesta
        response = cfn_client.list_stacks(
            StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        )
        
        for stack in response['StackSummaries']:
            if 'medical-analytics-ingestion' in stack['StackName'].lower():
                print(f"Stack de ingesta encontrado: {stack['StackName']}")
                
                # Obtener las salidas del stack
                outputs = cfn_client.describe_stacks(
                    StackName=stack['StackName']
                )['Stacks'][0].get('Outputs', [])
                
                # Buscar la URL del API Gateway en las salidas
                for output in outputs:
                    if 'ApiGatewayUrl' in output['OutputKey']:
                        api_url = output['OutputValue']
                        print(f"URL de API Gateway encontrada: {api_url}")
                        return api_url
        
        print("No se encontró la URL del API Gateway en las salidas del stack")
        return None
    
    except Exception as e:
        print(f"Error al buscar la URL de API Gateway: {str(e)}")
        return None

def get_api_key():
    """Obtiene la API Key del API Gateway."""
    print("Buscando API Key...")
    api_client = boto3.client('apigateway')
    
    try:
        # Listar todas las API Keys
        response = api_client.get_api_keys(includeValues=True)
        
        for key in response['items']:
            # Buscar una clave que tenga 'medical' o 'analytics' en el nombre
            if 'medical' in key.get('name', '').lower() or 'analytics' in key.get('name', '').lower():
                print(f"API Key encontrada: {key['name']}")
                return key['value']
        
        print("No se encontró una API Key adecuada")
        return None
    
    except Exception as e:
        print(f"Error al buscar API Key: {str(e)}")
        return None

def update_frontend_html(bucket_name, api_url, api_key):
    """Actualiza el archivo index.html en el bucket S3 para usar la URL correcta."""
    print(f"Actualizando index.html en bucket {bucket_name}...")
    s3_client = boto3.client('s3')
    
    try:
        # Descargar el archivo index.html
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key='index.html'
        )
        html_content = response['Body'].read().decode('utf-8')
        
        print("Archivo index.html descargado correctamente")
        
        # Verificar si hay tokens no resueltos
        token_pattern = r'\$\{Token\[TOKEN\.\d+\]\}'
        if re.search(token_pattern, html_content):
            print("Se encontraron tokens CDK no resueltos en el HTML")
            
            # Actualizar la URL de la API
            if api_url:
                # Asegurarse de que termina con "/"
                if not api_url.endswith('/'):
                    api_url += '/'
                
                api_endpoint = f"{api_url}upload"
                print(f"Endpoint de API que se usará: {api_endpoint}")
                
                # Buscar cualquier URL de API en el HTML, incluyendo las que contienen tokens
                api_url_pattern = r'https://[^\'"]*(?:execute-api|amazonaws)[^\'"]*'
                html_content = re.sub(api_url_pattern, api_endpoint, html_content)
                
                # También buscar específicamente el patrón mostrado en el error
                token_api_pattern = r'https://\$\{Token\[TOKEN\.\d+\]\}\.execute-api\.[^\'"]+'
                html_content = re.sub(token_api_pattern, api_endpoint, html_content)
                
                # También actualizar cualquier variable o constante JavaScript que contenga la URL
                js_api_pattern = r'(const\s+API_URL\s*=\s*[\'"]).+?([\'"])'
                html_content = re.sub(js_api_pattern, f'\\1{api_endpoint}\\2', html_content)
                
                print("URL de API Gateway actualizada en el HTML")
            
            # Actualizar la API Key
            if api_key:
                # Buscar y reemplazar cualquier referencia a API Key que contenga tokens
                api_key_pattern = r'([\'"]\s*x-api-key[\'"]:\s*[\'"])\$\{Token\[TOKEN\.\d+\]\}([\'"])'
                html_content = re.sub(api_key_pattern, f'\\1{api_key}\\2', html_content)
                
                # También buscar cualquier variable JavaScript que pueda contener la API Key
                js_api_key_pattern = r'(const\s+API_KEY\s*=\s*[\'"]).+?([\'"])'
                html_content = re.sub(js_api_key_pattern, f'\\1{api_key}\\2', html_content)
                
                # También buscar el patrón literal mostrado en la plantilla
                html_content = html_content.replace("{{API_KEY}}", api_key)
                
                print("API Key actualizada en el HTML")
            
            # Guardar el archivo actualizado
            s3_client.put_object(
                Bucket=bucket_name,
                Key='index.html',
                Body=html_content,
                ContentType='text/html'
            )
            
            print("Archivo index.html actualizado y guardado correctamente")
            return True
        else:
            print("No se encontraron tokens CDK no resueltos en el HTML. Es posible que el archivo ya esté actualizado.")
            
            # Aún así, verificar si la URL de la API y la API Key son correctas
            if api_url and api_key:
                # Actualizar de todas formas para asegurarnos
                if not api_url.endswith('/'):
                    api_url += '/'
                api_endpoint = f"{api_url}upload"
                
                # Buscar y reemplazar la URL de la API y la API Key
                html_content = html_content.replace("{{API_ENDPOINT}}", api_endpoint)
                html_content = html_content.replace("{{API_KEY}}", api_key)
                
                # Guardar el archivo actualizado
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key='index.html',
                    Body=html_content,
                    ContentType='text/html'
                )
                
                print("Archivo index.html actualizado con URL y API Key correctas")
                return True
            
            return False
    
    except Exception as e:
        print(f"Error al actualizar index.html: {str(e)}")
        return False

def invalidate_cloudfront_cache():
    """Invalida la caché de CloudFront para que los cambios se apliquen de inmediato."""
    print(f"Invalidando caché de CloudFront para distribución {DISTRIBUTION_ID}...")
    cloudfront_client = boto3.client('cloudfront')
    
    try:
        # Crear una invalidación para index.html
        response = cloudfront_client.create_invalidation(
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
        print(f"Invalidación de caché creada con ID: {invalidation_id}")
        print("La invalidación puede tardar unos minutos en completarse")
        return True
    
    except Exception as e:
        print(f"Error al invalidar caché de CloudFront: {str(e)}")
        print("NOTA: Aunque ocurrió un error al invalidar la caché, los cambios en el archivo HTML ya se aplicaron.")
        print("Puede tardar hasta 24 horas en propagarse o hasta que la caché expire.")
        return False

def main():
    print("=== Script de Corrección de URL de API en Frontend ===")
    
    # Buscar el bucket S3 que contiene el frontend
    bucket_name = find_frontend_bucket()
    if not bucket_name:
        print("No se pudo encontrar el bucket S3 del frontend")
        sys.exit(1)
    
    # Obtener la URL del API Gateway
    api_url = get_api_gateway_url()
    if not api_url:
        print("No se pudo obtener la URL del API Gateway")
        print("Por favor, proporciona la URL manualmente:")
        api_url = input("URL del API Gateway (ej. https://abcdef123.execute-api.us-east-2.amazonaws.com/dev/): ")
        if not api_url:
            print("No se proporcionó una URL válida")
            sys.exit(1)
    
    # Obtener la API Key
    api_key = get_api_key()
    if not api_key:
        print("No se pudo obtener la API Key")
        print("Por favor, proporciona la API Key manualmente:")
        api_key = input("API Key: ")
        if not api_key:
            print("No se proporcionó una API Key válida")
            sys.exit(1)
    
    # Actualizar el archivo HTML
    if not update_frontend_html(bucket_name, api_url, api_key):
        print("No se pudo actualizar el archivo HTML")
        sys.exit(1)
    
    # Invalidar la caché de CloudFront
    invalidate_cloudfront_cache()
    
    print("\n=== Correcciones completadas ===")
    print("El archivo HTML del frontend ha sido actualizado con la URL correcta del API Gateway y la API Key.")
    print(f"Por favor, intenta acceder nuevamente a la aplicación a través de CloudFront: https://{DISTRIBUTION_ID}.cloudfront.net/")
    print("NOTA: Es posible que tengas que esperar unos minutos para que los cambios se propaguen completamente.")
    print("Si los problemas persisten, limpia la caché de tu navegador o abre la aplicación en una ventana de incógnito.")

if __name__ == "__main__":
    main()
