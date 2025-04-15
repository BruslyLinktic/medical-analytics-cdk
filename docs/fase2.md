# Fase 2: Implementación de la Capa de Ingesta de Datos

## Objetivo

Desarrollar los componentes para ingestar datos médicos tanto desde la API del cliente como a través de una interfaz web para carga de archivos Excel.

## Tareas Completadas

- [x] Implementación de Componente de Ingesta API
- [x] Implementación de API Gateway para Carga de Archivos
- [x] Desarrollo de Función Lambda para Procesamiento de Archivos
- [x] Creación de Frontend Simple para Carga de Archivos
- [x] Configuración de Seguridad para Componentes de Ingesta

## Detalles de Implementación

### 1. Componente de Ingesta API

Se ha implementado una función Lambda (`medical-analytics-api-ingestion`) que se conecta a la API del cliente, recupera los datos médicos y los almacena en el bucket S3 en la ruta `raw/api/{YYYY-MM-DD}/{TIMESTAMP}_{REQUEST_ID}_data.json`.

**Características principales**:
- Ejecución programada 4 veces al día (9:00 AM, 1:00 PM, 5:00 PM, 9:00 PM UTC)
- Sistema de reintentos (máximo 3) en caso de fallo de conexión
- Almacenamiento particionado por fecha
- Registro de metadatos de ejecución (tiempo de inicio/fin, registros procesados, errores)
- Logging detallado para monitoreo y diagnóstico

### 2. API Gateway para Carga de Archivos

Se ha implementado una API REST con AWS API Gateway que expone un endpoint `/upload` para recibir archivos Excel desde el frontend:

**Características principales**:
- Método POST con autenticación mediante API key
- Configuración CORS para permitir llamadas desde el frontend
- Límites de tasa para prevenir abusos (10 solicitudes por segundo, ráfaga de 20)
- Cuota diaria de 100 solicitudes

### 3. Función Lambda para Procesamiento de Archivos

Se ha implementado una función Lambda (`medical-analytics-file-processor`) que recibe los archivos Excel enviados a través del API Gateway, los valida, y los almacena en S3 en la ruta `raw/excel/{YYYY-MM-DD}/{TIMESTAMP}_{REQUEST_ID}_{FILENAME}`.

**Características principales**:
- Validación de tipo de archivo (solo .xlsx y .xls permitidos)
- Validación de tamaño (límite de 10MB)
- Validación de estructura de datos (presencia de columnas requeridas)
- Sanitización de nombres de archivo para prevenir problemas de seguridad
- Registro de metadatos (IP de origen, agente de usuario, tamaño del archivo)
- Notificaciones de error mediante SNS para monitoreo

### 4. Frontend para Carga de Archivos

Se ha desarrollado una interfaz web simple alojada en un bucket S3 configurado como sitio web estático:

**Características principales**:
- Interfaz de usuario intuitiva con funcionalidad de arrastrar y soltar
- Validación en el lado del cliente para tipos de archivo y tamaño
- Barra de progreso para visualizar el proceso de carga
- Mensajes de estado claros (éxito/error)
- Instrucciones de uso para los usuarios

### 5. Seguridad Implementada

- **Autenticación**:
  - API Gateway protegida con API key
  - Permisos IAM con principio de mínimo privilegio

- **Validación de Datos**:
  - Validación de tipos de archivo permitidos
  - Sanitización de nombres de archivo
  - Validación de estructura de datos

- **Protección contra Abusos**:
  - Límites de tasa configurados en API Gateway
  - Cuotas de uso diarias
  - Tamaño máximo de archivo establecido

- **Monitoreo**:
  - Tópico SNS para notificaciones de error
  - Logging detallado en CloudWatch
  - Registro de metadatos de cada transacción para auditoría

## Arquitectura de la Solución

La capa de ingesta implementa dos flujos principales:

1. **Ingesta Automática desde API**:
   ```
   EventBridge (Trigger) -> Lambda (API Ingestion) -> API Externa -> S3 (raw/api/)
   ```

2. **Carga Manual de Archivos**:
   ```
   Frontend (S3 Website) -> API Gateway -> Lambda (File Processor) -> S3 (raw/excel/)
                                                   |
                                                   V
                                               SNS (Errores)
   ```

## Comandos para Desplegar

```bash
# Sintetizar la aplicación CDK
cdk synth

# Desplegar los recursos
cdk deploy --all

# Desplegar solo el stack de ingesta
cdk deploy medical-analytics-ingestion-dev
```

## Pruebas de la Capa de Ingesta

### Prueba de la función de ingesta API
```bash
# Invocar la función Lambda directamente
aws lambda invoke --function-name medical-analytics-api-ingestion --payload '{}' response.json
```

### Prueba de la API de carga de archivos
```bash
# Obtener el endpoint de API Gateway y API key
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
API_KEY=$(aws apigateway get-api-keys --name-query medical-analytics-api-key --include-values --query "items[0].value" --output text)

# Enviar un archivo de prueba
curl -X POST \
  $API_ENDPOINT/upload \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

## Frontend

El frontend está disponible en la siguiente URL después del despliegue:
```
http://medical-analytics-frontend-dev.s3-website-{REGION}.amazonaws.com
```

## Siguientes Pasos

Después de desplegar esta fase, se puede proceder a la Fase 3 para implementar la capa de procesamiento ETL, que incluirá:
- Configuración de AWS Glue Data Catalog
- Desarrollo de Crawler de AWS Glue
- Desarrollo de Script ETL para AWS Glue
- Configuración de Trabajo de AWS Glue
