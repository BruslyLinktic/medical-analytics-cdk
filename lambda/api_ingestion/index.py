import json
import os
import boto3
import requests
import logging
import datetime
import uuid

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar clientes de AWS
s3 = boto3.client('s3')

# Configuración
BUCKET_NAME = os.environ.get('BUCKET_NAME')
API_ENDPOINT = os.environ.get('API_ENDPOINT')
API_KEY = os.environ.get('API_KEY')
MAX_RETRIES = 3

def handler(event, context):
    """
    Función que consume la API del cliente y almacena los datos en S3.
    Se ejecuta periódicamente a través de EventBridge.
    
    Args:
        event (dict): Evento de EventBridge
        context (LambdaContext): Contexto de ejecución de Lambda
    
    Returns:
        dict: Resultado de la ejecución
    """
    try:
        logger.info(f"Iniciando proceso de ingesta desde API: {datetime.datetime.now()}")
        
        # Obtener la fecha actual para la partición
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        request_id = str(uuid.uuid4())
        
        # Intentar obtener datos de la API con reintentos
        data = fetch_api_data(MAX_RETRIES)
        
        if not data:
            return {
                'statusCode': 500,
                'body': json.dumps('Error al obtener datos de la API después de reintentos')
            }
        
        # Construir ruta de destino en S3
        s3_key = f"raw/api/{today}/{timestamp}_{request_id}_data.json"
        
        # Guardar datos en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        
        logger.info(f"Datos guardados exitosamente en s3://{BUCKET_NAME}/{s3_key}")
        
        # Registrar metadatos de la ejecución
        metadata = {
            'timestamp_inicio': datetime.datetime.now().isoformat(),
            'timestamp_fin': datetime.datetime.now().isoformat(),
            'registros_procesados': len(data) if isinstance(data, list) else 1,
            'errores': 0,
            'request_id': request_id
        }
        
        # Guardar metadatos en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"raw/api/{today}/{timestamp}_{request_id}_metadata.json",
            Body=json.dumps(metadata),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ingesta completada exitosamente',
                'records_processed': metadata['registros_procesados'],
                's3_location': f"s3://{BUCKET_NAME}/{s3_key}"
            })
        }
    
    except Exception as e:
        logger.error(f"Error en la ingesta de datos: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        }

def fetch_api_data(max_retries):
    """
    Obtiene datos de la API con reintentos en caso de fallo.
    
    Args:
        max_retries (int): Número máximo de reintentos
    
    Returns:
        dict/list: Datos obtenidos de la API
    """
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt + 1} de {max_retries} para obtener datos de la API")
            response = requests.get(API_ENDPOINT, headers=headers, timeout=30)
            response.raise_for_status()  # Levantar excepción si hay error HTTP
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error en intento {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"Se agotaron los reintentos. Último error: {str(e)}")
                return None
    
    return None
