#!/usr/bin/env python3
import os

import aws_cdk as cdk

from medical_analytics.storage_stack import StorageStack

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

# Aplicar tags a todos los recursos del stack
for key, value in tags.items():
    cdk.Tags.of(storage_stack).add(key, value)

app.synth()
