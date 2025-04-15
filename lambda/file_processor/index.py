import json
import os
import boto3
import base64
import logging
import datetime
import uuid
import re
import io
import pandas as pd
from botocore.exceptions import ClientError

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar clientes de AWS
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Configuración
BUCKET_NAME = os.environ.get('BUCKET_NAME')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB en bytes
ALLOWED_EXTENSIONS = ['xlsx', 'xls']
ERROR_TOPIC_ARN = os.environ.get('ERROR_TOPIC_ARN')
REQUIRED_COLUMNS = ['NUMDOC_PACIENTE', 'FECHA_FOLIO', 'NOMBRE_PACIENTE', 'DIAGNÓSTICO']

def handler(event, context):
    """
    Función para procesar archivos Excel recibidos a través de API Gateway.
    
    Args:
        event (dict): Evento de API Gateway
        context (LambdaContext): Contexto de ejecución de Lambda
    
    Returns:
        dict: Respuesta para API Gateway
    """
    try:
        logger.info("Iniciando procesamiento de archivo")
        
        # Validar el cuerpo de la solicitud
        if 'body' not in event:
            return build_response(400, 'No se encontró el cuerpo de la solicitud')
        
        # Si el body viene como string (dependiendo de la configuración de API Gateway)
        body = event['body']
        if isinstance(body, str):
            body = json.loads(body)
        
        # Obtener datos del archivo
        if 'file' not in body or 'filename' not in body:
            return build_response(400, 'El cuerpo debe contener "file" y "filename"')
        
        file_content_b64 = body['file']
        original_filename = body['filename']
        
        # Validar nombre y extensión del archivo
        if not is_valid_filename(original_filename):
            return build_response(400, 'Nombre de archivo inválido o extensión no permitida')
        
        # Decodificar el contenido del archivo
        try:
            file_content = base64.b64decode(file_content_b64)
        except Exception:
            return build_response(400, 'Error al decodificar el contenido del archivo')
        
        # Validar tamaño del archivo
        if len(file_content) > MAX_FILE_SIZE:
            return build_response(400, f'El archivo excede el tamaño máximo permitido ({MAX_FILE_SIZE/1024/1024}MB)')
        
        # Validar estructura del archivo Excel
        validation_result = validate_excel_structure(file_content)
        if not validation_result['valid']:
            return build_response(400, f'Estructura de archivo inválida: {validation_result["message"]}')
        
        # Preparar para almacenamiento en S3
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        sanitized_filename = sanitize_filename(original_filename)
        request_id = str(uuid.uuid4())
        
        # Construir ruta de destino en S3
        s3_key = f"raw/excel/{today}/{timestamp}_{request_id}_{sanitized_filename}"
        
        # Guardar archivo en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if sanitized_filename.endswith('.xlsx') else 'application/vnd.ms-excel'
        )
        
        logger.info(f"Archivo guardado exitosamente en s3://{BUCKET_NAME}/{s3_key}")
        
        # Registrar metadatos para auditoría
        client_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        user_agent = event.get('requestContext', {}).get('identity', {}).get('userAgent', 'unknown')
        
        metadata = {
            'original_filename': original_filename,
            'timestamp': datetime.datetime.now().isoformat(),
            'client_ip': client_ip,
            'user_agent': user_agent,
            'file_size_bytes': len(file_content),
            'request_id': request_id
        }
        
        # Guardar metadatos en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"raw/excel/{today}/{timestamp}_{request_id}_metadata.json",
            Body=json.dumps(metadata),
            ContentType='application/json'
        )
        
        return build_response(200, {
            'message': 'Archivo procesado exitosamente',
            's3_location': f"s3://{BUCKET_NAME}/{s3_key}",
            'request_id': request_id
        })
    
    except Exception as e:
        logger.error(f"Error en el procesamiento del archivo: {str(e)}")
        
        # Enviar notificación de error para su revisión
        if ERROR_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=ERROR_TOPIC_ARN,
                    Subject=f"Error en procesamiento de archivo",
                    Message=f"Se produjo un error al procesar un archivo:\n{str(e)}"
                )
            except Exception as sns_error:
                logger.error(f"Error al enviar notificación: {str(sns_error)}")
        
        return build_response(500, {
            'message': 'Error interno al procesar el archivo',
            'error_id': str(uuid.uuid4())
        })

def is_valid_filename(filename):
    """
    Valida que el nombre de archivo tenga una extensión permitida y caracteres válidos.
    
    Args:
        filename (str): Nombre del archivo a validar
    
    Returns:
        bool: True si el nombre es válido, False en caso contrario
    """
    # Verificar que el nombre no esté vacío
    if not filename or len(filename) < 5:  # Al menos "a.xls"
        return False
    
    # Verificar extensión
    extension = filename.split('.')[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False
    
    # Verificar caracteres válidos (letras, números, puntos, guiones, espacios)
    if not re.match(r'^[a-zA-Z0-9\-_\.\s]+$', filename):
        return False
    
    return True

def sanitize_filename(filename):
    """
    Limpia el nombre de archivo para evitar problemas de seguridad.
    
    Args:
        filename (str): Nombre del archivo a limpiar
    
    Returns:
        str: Nombre de archivo limpio
    """
    # Remover caracteres especiales manteniendo letras, números, puntos, guiones, underscore
    clean_name = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)
    
    # Asegurar que tenga la extensión correcta
    extension = clean_name.split('.')[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        # Esto no debería ocurrir si ya validamos antes, pero por si acaso
        clean_name = clean_name + '.xlsx'
    
    return clean_name

def validate_excel_structure(file_content):
    """
    Valida que el archivo Excel tenga la estructura esperada.
    
    Args:
        file_content (bytes): Contenido del archivo Excel
    
    Returns:
        dict: Resultado de la validación con 'valid' (bool) y 'message' (str)
    """
    try:
        # Cargar el archivo Excel en un DataFrame
        excel_file = io.BytesIO(file_content)
        df = pd.read_excel(excel_file)
        
        # Verificar que no esté vacío
        if df.empty:
            return {'valid': False, 'message': 'El archivo no contiene datos'}
        
        # Verificar columnas requeridas
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            return {'valid': False, 'message': f'Faltan columnas requeridas: {", ".join(missing_columns)}'}
        
        # Verificar que no haya macros (esto es simplificado, la verificación real puede ser más compleja)
        # Una verificación real podría implicar análisis más profundo del archivo
        
        return {'valid': True, 'message': 'Estructura válida'}
    
    except Exception as e:
        return {'valid': False, 'message': f'Error al validar estructura: {str(e)}'}

def build_response(status_code, body):
    """
    Construye una respuesta para API Gateway.
    
    Args:
        status_code (int): Código de estado HTTP
        body (dict/str): Cuerpo de la respuesta
    
    Returns:
        dict: Respuesta formateada para API Gateway
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Para CORS
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps(body) if isinstance(body, dict) else json.dumps({'message': body})
    }
