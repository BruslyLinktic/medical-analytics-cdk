# Sistema de Analítica Médica con AWS CDK

Este proyecto implementa un sistema completo de analítica para datos médicos recolectados en campañas de salud. Utiliza una arquitectura serverless implementada como código usando AWS CDK con Python.

## Arquitectura del Sistema

El sistema está dividido en varias capas:

1. **Capa de Almacenamiento**: Bucket S3 con estructura organizada, encriptación y políticas de seguridad.
2. **Capa de Ingesta**: API Gateway + Lambda para cargar archivos Excel y función programada para consumir API externa.
3. **Capa de Procesamiento**: Trabajos ETL con AWS Glue (a implementar en fases posteriores).
4. **Capa de Análisis**: Consultas con Athena y visualizaciones con QuickSight (a implementar en fases posteriores).
5. **Capa de Distribución (CDN)**: CloudFront para servir el frontend de forma segura y con soporte CORS.

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
├── deploy.py                   # Script personalizado para despliegue
├── test_cors.py                # Herramienta para probar configuración CORS
├── medical_analytics/          # Módulos del proyecto
│   ├── storage_stack.py        # Stack de almacenamiento
│   ├── ingestion_stack.py      # Stack de ingesta
│   └── cdn_stack/              # Stack de CDN (CloudFront)
│       └── cdn_stack.py        # Implementación del stack de CDN
├── lambda/                     # Código para funciones Lambda
│   ├── api_ingestion/          # Lambda para consumir API externa
│   └── file_processor/         # Lambda para procesar archivos subidos
└── frontend/                   # Frontend para carga de archivos
    └── index.html              # Interfaz web simple
```

## Despliegue

### Despliegue Automatizado (Recomendado)

Usar el script de despliegue automatizado:

```bash
# Dar permisos de ejecución al script
chmod +x deploy.py

# Desplegar todos los stacks en ambiente dev
./deploy.py --stage dev

# Opciones avanzadas
./deploy.py --help
```

### Despliegue Manual

Para desplegar manualmente los stacks:

```bash
# Desplegar stack de almacenamiento
cdk deploy medical-analytics-storage-dev

# Desplegar stack de ingesta
cdk deploy medical-analytics-ingestion-dev

# Desplegar stack de CDN
cdk deploy medical-analytics-cdn-dev
```

## Pruebas de CORS

Una vez desplegado el sistema, puedes verificar la configuración CORS usando:

```bash
# Dar permisos de ejecución al script
chmod +x test_cors.py

# Probar la configuración CORS (reemplazar con la URL real)
./test_cors.py https://tu-api-id.execute-api.us-east-1.amazonaws.com/prod/upload --api-key tu-api-key
```

## Acceso al Frontend

Una vez completado el despliegue, el frontend estará disponible a través de CloudFront. La URL se mostrará en las salidas del despliegue:

```bash
# Ver las salidas del stack de CDN
aws cloudformation describe-stacks --stack-name medical-analytics-cdn-dev --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text
```

## Solución de Problemas Comunes

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
       bucket_name="medical-analytics-project-dev-unique",  # Cambiar nombre
       # Otras propiedades...
   )
   ```

### Problemas con CORS o Acceso a CloudFront

Si encuentras problemas de CORS al usar el frontend:

1. Verifica que estás accediendo a través de la URL de CloudFront (no directamente al bucket S3)
2. Usa la herramienta `test_cors.py` para diagnosticar problemas
3. Asegúrate que en el frontend se está utilizando la API Key correcta

### Error 403 Forbidden en CloudFront

Si recibes un error "403 Forbidden" al acceder a la URL de CloudFront:

1. Ejecuta el script de corrección de permisos:
   ```bash
   # Dar permisos de ejecución al script
   chmod +x fix_cloudfront.sh
   
   # Ejecutar el script
   ./fix_cloudfront.sh
   ```

2. Este script corrige la configuración de permisos entre CloudFront y el bucket S3 que aloja el frontend.

3. Si el problema persiste, consulta la sección correspondiente en `TROUBLESHOOTING.md` para más detalles.

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
- Implementación de monitoreo y seguridad (Fase 5)
- Completar la documentación y pruebas (Fase 6)
