#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import aws_secretsmanager as secretsmanager

from medical_analytics.storage_stack import StorageStack
from medical_analytics.lambda_layer_stack import LambdaLayerStack
from medical_analytics.ingestion_stack import IngestionStack
from medical_analytics.cdn_stack.cdn_stack import CDNStack

app = cdk.App()

# Definición de variables de entorno
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')
)

# Tags comunes para todos los recursos
tags = {
    'Project': 'MedicalAnalytics',
    'Environment': 'Dev',
    'Owner': 'MedicalAnalyticsTeam'
}

# Despliegue del stack de Lambda Layers (debe ir primero para poder ser referenciado)
lambda_layer_stack = LambdaLayerStack(
    app,
    "medical-analytics-layers-dev",
    env=env,
    description="Stack de Lambda Layers para el sistema de analítica médica"
)

# Despliegue del stack de almacenamiento
storage_stack = StorageStack(
    app, 
    "medical-analytics-storage-dev",
    env=env,
    description="Stack de almacenamiento para el sistema de analítica médica"
)

# Crear un tópico SNS para errores a nivel de aplicación en el stack de almacenamiento
# Esto evita dependencias cíclicas
sns_topic = storage_stack.create_error_topic("MedicalAnalyticsErrorTopic")

# Despliegue del stack de ingesta (ahora con referencia a los layers)
ingestion_stack = IngestionStack(
    app,
    "medical-analytics-ingestion-dev",
    storage_bucket=storage_stack.bucket,
    storage_key_arn=storage_stack.encryption_key_arn,
    ingestion_role=storage_stack.ingestion_role,
    error_topic=sns_topic,
    pandas_layer=lambda_layer_stack.pandas_layer,
    common_layer=lambda_layer_stack.common_layer,
    env=env,
    description="Stack de ingesta para el sistema de analítica médica"
)

# Para acceder a la API Key, necesitamos recuperarla desde el secreto
api_key_value = None
if hasattr(ingestion_stack, 'api_key_secret') and ingestion_stack.api_key_secret:
    # En producción, este valor se recuperaría de Secrets Manager
    # Para desarrollo, lo configuramos manualmente
    api_key_secret = ingestion_stack.api_key_secret
    try:
        # Intentar acceder al valor para pasarlo al frontend
        api_key_value = api_key_secret.secret_value.to_string()
    except Exception:
        # Si no podemos acceder directamente (es un constructo CDK), 
        # usaremos una salida para recuperarlo después del despliegue
        api_key_value = "${aws secretsmanager get-secret-value --secret-id " + api_key_secret.secret_name + " --query 'SecretString' --output text}"

# Despliegue del stack de CDN - ahora creamos el frontend dentro de este stack
cdn_stack = CDNStack(
    app,
    "medical-analytics-cdn-dev",
    api_gateway_url=ingestion_stack.api_gateway_url,
    api_key_value=api_key_value or "placeholder-api-key",  # Placeholder si no podemos obtener el valor
    env=env,
    description="Stack de CDN para la interfaz web del sistema de analítica médica"
)

# Definir dependencias explícitas
storage_stack.add_dependency(lambda_layer_stack)  # Storage necesita los layers para sus roles
ingestion_stack.add_dependency(storage_stack)
ingestion_stack.add_dependency(lambda_layer_stack)
cdn_stack.add_dependency(ingestion_stack)

# Aplicar tags a todos los recursos del stack
for stack in [lambda_layer_stack, storage_stack, ingestion_stack, cdn_stack]:
    for key, value in tags.items():
        cdk.Tags.of(stack).add(key, value)

app.synth()
