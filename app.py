#!/usr/bin/env python3
import os

import aws_cdk as cdk

from medical_analytics.storage_stack import StorageStack
from medical_analytics.ingestion_stack import IngestionStack

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

# Despliegue del stack de ingesta
ingestion_stack = IngestionStack(
    app,
    "medical-analytics-ingestion-dev",
    storage_bucket=storage_stack.bucket,
    storage_key_arn=storage_stack.encryption_key_arn,
    ingestion_role=storage_stack.ingestion_role,
    error_topic=sns_topic,
    env=env,
    description="Stack de ingesta para el sistema de analítica médica"
)

# Definir dependencia explícita
ingestion_stack.add_dependency(storage_stack)

# Aplicar tags a todos los recursos del stack
for stack in [storage_stack, ingestion_stack]:
    for key, value in tags.items():
        cdk.Tags.of(stack).add(key, value)

app.synth()
