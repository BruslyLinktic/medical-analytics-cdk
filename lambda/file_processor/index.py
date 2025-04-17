import json
import os
import boto3
import base64
import logging
import datetime
import uuid
import re
import traceback

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar clientes de AWS
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Configuración
BUCKET_NAME = os.environ.get('BUCKET_NAME')
ERROR_TOPIC_ARN = os.environ.get('ERROR_TOPIC_ARN')


def handler(event, context):
    """
    Función Lambda para decodificar un archivo Base64 y subirlo a S3.
    No realiza validaciones adicionales.

    Args:
        event (dict): Evento de API Gateway
        context (LambdaContext): Contexto de ejecución Lambda

    Returns:
        dict: Respuesta HTTP
    """
    request_id = str(uuid.uuid4())
    try:
        logger.info(f"Inicio de procesamiento. Request ID: {request_id}")

        # Obtener y parsear el cuerpo
        body = event.get('body', '')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return build_response(400, 'Cuerpo de solicitud no es JSON válido')

        # Extraer datos de archivo
        encoded_file = body.get('file')
        original_filename = body.get('filename', request_id)

        if not encoded_file:
            return build_response(400, 'No se proporcionó contenido de archivo')

        # Decodificar Base64
        try:
            file_bytes = base64.b64decode(encoded_file)
        except Exception as e:
            logger.error(f"Error decodificando Base64: {e}")
            return build_response(400, 'Error al decodificar el archivo')

        # Sanitizar nombre de archivo
        sanitized_name = sanitize_filename(original_filename)

        # Generar clave S3 única
        now = datetime.datetime.utcnow()
        date_str = now.strftime('%Y-%m-%d')
        timestamp = now.strftime('%Y%m%dT%H%M%SZ')
        s3_key = f"uploads/{date_str}/{timestamp}_{request_id}_{sanitized_name}"

        # Subir a S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=guess_content_type(sanitized_name),
            Metadata={'request-id': request_id, 'original-filename': original_filename}
        )
        logger.info(f"Archivo subido: s3://{BUCKET_NAME}/{s3_key}")

        # Notificación de éxito (opcional)
        log_activity(request_id, context, s3_key)

        return build_response(200, {'message': 'Archivo subido correctamente', 's3_key': s3_key})

    except Exception as ex:
        err = str(ex)
        trace = traceback.format_exc()
        logger.error(f"Error interno: {err}")
        logger.error(trace)
        notify_error('InternalError', err, request_id, context.aws_request_id, trace)
        return build_response(500, {'message': 'Error interno al procesar el archivo', 'request_id': request_id})


def sanitize_filename(filename):
    """
    Reemplaza caracteres no válidos por guiones bajos.
    """
    return re.sub(r'[^a-zA-Z0-9\.\-_ ]', '_', filename)


def guess_content_type(filename):
    """
    Determina el ContentType según la extensión.
    """
    ext = filename.lower().split('.')[-1]
    if ext == 'xlsx':
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    if ext == 'xls':
        return 'application/vnd.ms-excel'
    return 'application/octet-stream'


def notify_error(error_type, error_message, request_id, lambda_request_id, stack_trace=None):
    """
    Envía una notificación de error a SNS si está configurado.
    """
    if not ERROR_TOPIC_ARN:
        logger.warning('ERROR_TOPIC_ARN no configurado, no se envía notificación')
        return
    message = {
        'error_type': error_type,
        'error_message': error_message,
        'request_id': request_id,
        'lambda_request_id': lambda_request_id,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    if stack_trace:
        message['stack_trace'] = stack_trace
    try:
        sns.publish(TopicArn=ERROR_TOPIC_ARN, Subject=f"Error Lambda: {error_type}", Message=json.dumps(message))
        logger.info('Notificación de error enviada')
    except Exception as e:
        logger.error(f"Fallo al enviar notificación SNS: {e}")


def log_activity(request_id, context, s3_key):
    """
    Registra un log básico de la subida en S3 para auditoría.
    """
    try:
        log_key = f"logs/{datetime.datetime.utcnow().strftime('%Y-%m-%d')}/upload_{request_id}.json"
        record = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'lambda_name': context.function_name,
            'lambda_request_id': context.aws_request_id,
            'request_id': request_id,
            's3_key': s3_key
        }
        s3.put_object(Bucket=BUCKET_NAME, Key=log_key, Body=json.dumps(record), ContentType='application/json')
    except Exception as e:
        logger.error(f"Error registrando actividad: {e}")


def build_response(status_code, body):
    """
    Construye la respuesta HTTP para API Gateway.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
