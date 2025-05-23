#!/usr/bin/env python3
import os

import aws_cdk as cdk

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

# Valor placeholder para la API key - se actualizará después del despliegue
api_key_value = "placeholder-api-key"

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
