# Sistema de Analítica Médica con AWS CDK

Este proyecto implementa un sistema completo de analítica para datos médicos recolectados en campañas de salud. Utiliza una arquitectura serverless implementada como código usando AWS CDK con Python.

## Arquitectura del Sistema

El sistema está dividido en varias capas:

1. **Capa de Almacenamiento**: Bucket S3 con estructura organizada, encriptación y políticas de seguridad.
2. **Capa de Ingesta**: API Gateway + Lambda para cargar archivos Excel y función programada para consumir API externa.
3. **Capa de Procesamiento**: Trabajos ETL con AWS Glue (a implementar en fases posteriores).
4. **Capa de Análisis**: Consultas con Athena y visualizaciones con QuickSight (a implementar en fases posteriores).
5. **Capa de Distribución (CDN)**: CloudFront para servir el frontend de forma segura y con soporte CORS.
6. **Capa de Lambda Layers**: Gestión de dependencias como pandas para las funciones Lambda.

## Requisitos Previos

- [Python 3.9+](https://www.python.org/downloads/)
- [AWS CLI](https://aws.amazon.com/cli/) configurado con credenciales adecuadas
- [AWS CDK](https://aws.amazon.com/cdk/) instalado (`npm install -g aws-cdk`)
- Virtualenv (`pip install virtualenv`)

## Configuración Inicial

1. Clonar el repositorio
   ```bash
   git clone <url-del-repositorio>
   cd medical-analytics-cdk
   ```

2. Crear y activar entorno virtual
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias
   ```bash
   pip install -r requirements.txt
   ```

4. Arrancar la aplicación CDK (solo primera vez)
   ```bash
   cdk bootstrap
   ```

## Estructura del Proyecto

```
medical-analytics-cdk/
├── app.py                      # Punto de entrada principal de CDK
├── scripts/                    # Scripts de utilidad para el proyecto
│   ├── deploy.sh               # Script automatizado de despliegue
│   └── fix_cloudfront_permissions.py  # Script para corrección de permisos
├── medical_analytics/          # Módulos del proyecto
│   ├── storage_stack.py        # Stack de almacenamiento
│   ├── ingestion_stack.py      # Stack de ingesta
│   ├── lambda_layer_stack.py   # Stack de capas Lambda
│   └── cdn_stack/              # Stack de CDN (CloudFront)
│       └── cdn_stack.py        # Implementación del stack de CDN
├── lambda/                     # Código para funciones Lambda
│   ├── api_ingestion/          # Lambda para consumir API externa
│   └── file_processor/         # Lambda para procesar archivos subidos
├── layers/                     # Definiciones de Lambda Layers
│   ├── pandas_layer/           # Layer para pandas y dependencias de Excel
│   └── common_layer/           # Layer para dependencias comunes
└── frontend/                   # Frontend para carga de archivos
    └── index.html              # Interfaz web simple
```

## Despliegue

### Despliegue Automatizado (Recomendado)

Usar el script de despliegue automatizado:

```bash
# Dar permisos de ejecución al script
chmod +x scripts/deploy.sh

# Desplegar todos los stacks en ambiente dev
./scripts/deploy.sh

# Opciones avanzadas
./scripts/deploy.sh --help
```

### Despliegue Manual

Para desplegar manualmente los stacks:

```bash
# Desplegar stack de Lambda Layers (debe ir primero)
cdk deploy medical-analytics-layers-dev

# Desplegar stack de almacenamiento
cdk deploy medical-analytics-storage-dev

# Desplegar stack de ingesta
cdk deploy medical-analytics-ingestion-dev

# Desplegar stack de CDN
cdk deploy medical-analytics-cdn-dev
```

## Acceso al Frontend

Una vez completado el despliegue, el frontend estará disponible a través de CloudFront. La URL se mostrará en las salidas del despliegue:

```bash
# Ver las salidas del stack de CDN
aws cloudformation describe-stacks --stack-name medical-analytics-cdn-dev --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text
```

## API Key para el Frontend

Para obtener la API Key necesaria para el frontend:

```bash
# Ver el comando para obtener la API Key
aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Outputs[?OutputKey=='GetApiKeyCommand'].OutputValue" --output text | bash
```

## Solución de Problemas Comunes

### Problema con Dependencias en Lambda

Las dependencias externas como pandas están incluidas en Lambda Layers. Si encuentras errores relacionados con módulos que faltan:

1. Verifica que el stack de Lambda Layers se haya desplegado correctamente:
   ```bash
   aws cloudformation describe-stacks --stack-name medical-analytics-layers-dev
   ```

2. Comprueba que las Lambdas estén configuradas para usar las capas (layers):
   ```bash
   aws lambda get-function --function-name medical-analytics-file-processor --query "Configuration.Layers"
   ```

### Bucket S3 ya existe

Si el bucket S3 ya existe, tienes dos opciones:

1. Eliminar el bucket existente:
   ```bash
   aws s3 rb s3://medical-analytics-project-dev --force
   ```

2. Cambiar el nombre del bucket en el código (`storage_stack.py`):
   ```python
   bucket = s3.Bucket(
       self,
       "MedicalAnalyticsBucket",
       bucket_name=f"medical-analytics-project-{self.account}-{self.region}",  # Nombre único
       # Otras propiedades...
   )
   ```

### Problemas con CORS o Acceso a CloudFront

Si encuentras problemas de CORS al usar el frontend:

1. Verifica que estás accediendo a través de la URL de CloudFront (no directamente al bucket S3)
2. Comprueba que las cabeceras CORS estén configuradas correctamente en API Gateway

### Error 403 Forbidden en CloudFront

Si recibes un error "403 Forbidden" al acceder a la URL de CloudFront, el stack de CDN ha sido mejorado para configurar correctamente los permisos OAI. Si aún persisten problemas:

1. Verifica la política del bucket para el frontend:
   ```bash
   aws s3api get-bucket-policy --bucket nombre-del-bucket-frontend
   ```

2. Comprueba la configuración del OAI en CloudFront:
   ```bash
   aws cloudfront get-distribution --id ID-DE-DISTRIBUCION
   ```

## Seguridad

Este proyecto implementa varias mejoras de seguridad:

1. **Encriptación**: Todos los datos en S3 están encriptados usando KMS o encriptación S3 gestionada.
2. **Secretos**: Las API keys se gestionan con AWS Secrets Manager.
3. **HTTPS**: Todo el tráfico externo es HTTPS mediante CloudFront.
4. **IAM**: Roles con privilegios mínimos siguiendo el principio de menor privilegio.
5. **Monitoreo**: Alarmas CloudWatch para detección de errores y comportamientos anómalos.

## Limpieza

Para eliminar todos los recursos desplegados:

```bash
cdk destroy --all
```

Nota: La eliminación de algunos recursos (como los buckets S3) puede requerir pasos adicionales si contienen datos.

## Siguientes Pasos

Este despliegue implementa las Fases 1, 2 y parte de la 6 del plan de proyecto. Las próximas fases incluirán:

- Implementación de la capa de procesamiento ETL (Fase 3)
- Implementación de la capa de análisis y visualización (Fase 4)
- Implementación de monitoreo y seguridad avanzados (Fase 5)
- Completar la documentación y pruebas (Fase 6)
