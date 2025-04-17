import json
import os
import boto3
import requests
import logging
import datetime
import uuid
import traceback

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar clientes de AWS
s3 = boto3.client('s3')
# Otros clientes se inicializan cuando se necesitan

# Configuración
BUCKET_NAME = os.environ.get('BUCKET_NAME')
API_ENDPOINT = os.environ.get('API_ENDPOINT')
API_KEY = os.environ.get('API_KEY')  # API key hardcoded para desarrollo
ERROR_TOPIC_ARN = os.environ.get('ERROR_TOPIC_ARN', '')
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
        
        # Usar la API key directamente desde la variable de entorno
        # En una implementación final esto vendría de Secrets Manager
        api_key = API_KEY
        
        # Intentar obtener datos de la API con reintentos
        data = fetch_api_data(api_key, MAX_RETRIES)
        
        if not data:
            error_message = 'Error al obtener datos de la API después de reintentos'
            notify_error(error_message, context.aws_request_id)
            return {
                'statusCode': 500,
                'body': json.dumps(error_message)
            }
        
        # Construir ruta de destino en S3
        s3_key = f"raw/api/{today}/{timestamp}_{request_id}_data.json"
        
        # Guardar datos en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType='application/json',
            Metadata={
                'request-id': request_id,
                'lambda-request-id': context.aws_request_id,
                'source': 'api-ingestion'
            }
        )
        
        logger.info(f"Datos guardados exitosamente en s3://{BUCKET_NAME}/{s3_key}")
        
        # Registrar metadatos de la ejecución
        metadata = {
            'timestamp_inicio': datetime.datetime.now().isoformat(),
            'timestamp_fin': datetime.datetime.now().isoformat(),
            'registros_procesados': len(data) if isinstance(data, list) else 1,
            'errores': 0,
            'request_id': request_id,
            'lambda_request_id': context.aws_request_id,
            'api_endpoint': API_ENDPOINT  # No incluir la API key por seguridad
        }
        
        # Guardar metadatos en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"raw/api/{today}/{timestamp}_{request_id}_metadata.json",
            Body=json.dumps(metadata),
            ContentType='application/json'
        )
        
        # Registrar actividad para auditoría
        log_activity(
            action="api_ingestion_success",
            details={
                "records_processed": metadata['registros_procesados'],
                "s3_location": f"s3://{BUCKET_NAME}/{s3_key}"
            },
            request_id=request_id,
            context=context
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
        # Capturar detalles del error
        error_type = type(e).__name__
        error_message = str(e)
        stack_trace = traceback.format_exc()
        
        logger.error(f"Error en la ingesta de datos: {error_message}")
        logger.error(f"Stack trace: {stack_trace}")
        
        # Notificar el error
        notify_error(f"{error_type}: {error_message}", context.aws_request_id, stack_trace)
        
        # Registrar actividad de error
        log_activity(
            action="api_ingestion_error",
            details={
                "error_type": error_type,
                "error_message": error_message
            },
            request_id=str(uuid.uuid4()),
            context=context
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {error_message}',
                'type': error_type,
                'request_id': context.aws_request_id
            })
        }

# def get_api_key_from_secret():
#     """
#     Código comentado: la opción de usar Secrets Manager ha sido removida
#     por simplicidad para desarrollo.
#     """
#     pass

def fetch_api_data(api_key, max_retries):
    """
    Obtiene datos de la API con reintentos en caso de fallo.
    
    Args:
        api_key (str): API key para autenticación
        max_retries (int): Número máximo de reintentos
    
    Returns:
        dict/list: Datos obtenidos de la API
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Medical-Analytics-Ingestion/1.0'
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

def notify_error(error_message, request_id, stack_trace=None):
    """
    Notifica un error a través de SNS.
    
    Args:
        error_message (str): Mensaje de error
        request_id (str): ID de la solicitud
        stack_trace (str, opcional): Traza de la pila de ejecución
    """
    if not ERROR_TOPIC_ARN:
        logger.warning("No se ha configurado ERROR_TOPIC_ARN. No se enviará notificación.")
        return
    
    try:
        # Inicializar cliente de SNS cuando se necesita
        sns = boto3.client('sns')
        
        message = {
            "error": error_message,
            "timestamp": datetime.datetime.now().isoformat(),
            "component": "api_ingestion_lambda",
            "request_id": request_id
        }
        
        if stack_trace:
            message["stack_trace"] = stack_trace
        
        sns.publish(
            TopicArn=ERROR_TOPIC_ARN,
            Subject=f"Error en ingesta de API - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            Message=json.dumps(message, indent=2)
        )
        
        logger.info(f"Notificación de error enviada a {ERROR_TOPIC_ARN}")
    
    except Exception as e:
        logger.error(f"Error al enviar notificación: {str(e)}")

def log_activity(action, details, request_id, context):
    """
    Registra actividad en S3 para auditoría.
    
    Args:
        action (str): Tipo de acción realizada
        details (dict): Detalles de la acción
        request_id (str): ID de la solicitud
        context (LambdaContext): Contexto de Lambda
    """
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        activity_log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "lambda_name": context.function_name,
            "lambda_version": context.function_version,
            "lambda_request_id": context.aws_request_id,
            "request_id": request_id,
            "details": details
        }
        
        # Guardar log en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"activity_logs/{today}/api_ingestion/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{request_id}.json",
            Body=json.dumps(activity_log),
            ContentType='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error al registrar actividad: {str(e)}")
