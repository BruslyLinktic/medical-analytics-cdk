# Estructura del Proyecto de Analítica Médica con AWS CDK

Este documento describe la estructura de carpetas y archivos del proyecto, explicando la función de cada componente principal.

## Estructura de Carpetas

```
medical-analytics-cdk/
├── app.py                     # Punto de entrada principal para CDK
├── cdk.json                   # Configuración de CDK
├── requirements.txt           # Dependencias Python del proyecto
├── README.md                  # Documentación general del proyecto
├── TROUBLESHOOTING.md         # Guía de solución de problemas
├── INSTRUCCIONES_DESPLIEGUE.md # Instrucciones para desplegar el proyecto
│
├── medical_analytics/         # Paquete principal del proyecto
│   ├── __init__.py
│   ├── storage_stack.py       # Stack para almacenamiento S3 y seguridad
│   ├── ingestion_stack.py     # Stack para ingesta de datos (API Gateway, Lambda)
│   └── cdn_stack/             # Stack para distribución CloudFront
│       ├── __init__.py
│       └── cdn_stack.py       # Implementación de CloudFront para frontend
│
├── frontend/                  # Archivos del frontend
│   └── index.html             # Página web para carga de archivos
│
├── lambda/                    # Código fuente para funciones Lambda
│   ├── api_consumer/          # Función para consumir API externa
│   └── file_processor/        # Función para procesar archivos subidos
│
├── scripts/                   # Scripts de utilidad y automatización
│   ├── fix_cloudfront_permissions.py  # Script para corregir permisos CloudFront-S3
│   └── otros scripts...
│
├── docs/                      # Documentación del proyecto
│   └── ESTRUCTURA_PROYECTO.md # Este archivo
│
└── tests/                     # Pruebas del proyecto
```

## Explicación de Componentes Principales

### Stacks de CDK

1. **StorageStack** (`storage_stack.py`)
   - Implementa el bucket S3 para almacenamiento de datos médicos
   - Configura encriptación KMS para datos sensibles
   - Define estructura de carpetas (raw, cleaned, curated)
   - Configura políticas de seguridad y roles IAM base

2. **IngestionStack** (`ingestion_stack.py`)
   - Implementa API Gateway para recibir archivos Excel
   - Configura función Lambda para consumir API externa
   - Configura función Lambda para procesar archivos subidos
   - Implementa EventBridge para programar ejecuciones periódicas

3. **CDNStack** (`cdn_stack/cdn_stack.py`)
   - Implementa distribución CloudFront para la interfaz web
   - Configura S3 para alojar el frontend
   - Implementa políticas CORS y seguridad
   - Despliega archivos HTML/JS del frontend

### Frontend

- **index.html**: Interfaz web simple para carga de archivos Excel. Incluye:
  - Formulario de carga de archivos con validación
  - Integración con API Gateway para enviar archivos
  - Indicadores visuales de progreso y estado
  - Instrucciones para usuarios

### Scripts de Utilidad

- **fix_cloudfront_permissions.py**: Corrige permisos entre CloudFront y S3
  - Identifica distribuciones CloudFront del proyecto
  - Configura políticas de bucket S3 adecuadas
  - Asegura que CloudFront pueda acceder al contenido en S3

### Arquitectura General

```
  [Usuario] -------> [CloudFront] -------> [Bucket S3 Frontend]
     |
     v
[API Gateway] -------> [Lambda]  -------> [Bucket S3 Datos]
                           |                    ^
                           v                    |
                    [API Externa] --------> [EventBridge]
```

## Relación entre Componentes

- **Flujo de ingesta de datos vía web**:
  1. Usuario accede a la interfaz web a través de CloudFront
  2. Sube archivo Excel a través del formulario
  3. API Gateway recibe el archivo
  4. Lambda procesa el archivo y lo almacena en S3 (raw/excel)

- **Flujo de ingesta de datos vía API**:
  1. EventBridge dispara función Lambda según programación
  2. Lambda consulta API externa y obtiene datos
  3. Lambda formatea y almacena datos en S3 (raw/api)

## Convenciones de Nombrado

- **Buckets S3**:
  - `medical-analytics-project-dev`: Almacenamiento principal de datos
  - `medical-analytics-frontend-dev`: Archivos del frontend

- **Roles IAM**:
  - `MedicalAnalyticsIngestionRole`: Para funciones de ingesta
  - `MedicalAnalyticsETLRole`: Para procesamiento ETL
  - `MedicalAnalyticsVisualizationRole`: Para análisis y visualización

- **Tags**:
  - Project: MedicalAnalytics
  - Environment: Dev/Test/Prod
  - Owner: MedicalAnalyticsTeam
