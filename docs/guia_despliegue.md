# Guía de Despliegue del Sistema de Analítica Médica

Esta guía te ayudará a desplegar correctamente el sistema de analítica médica, evitando las dependencias cíclicas.

## 1. Preparación del Entorno

```bash
# Entrar al directorio del proyecto
cd /Users/brandowleon/medical-analytics-cdk/

# Activar el entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Dar permisos de ejecución a los scripts
chmod +x scripts/*.sh
```

## 2. Bootstrap de AWS CDK

Antes de desplegar los stacks, es necesario hacer bootstrap de AWS CDK:

```bash
cdk bootstrap
```

## 3. Despliegue de los Stacks

### Opción 1: Despliegue Automatizado (Recomendado)

```bash
# Ejecutar el script de despliegue automatizado
./scripts/deploy.sh
```

### Opción 2: Despliegue Manual

Si prefieres desplegar manualmente cada stack:

```bash
# 1. Primero desplegar el stack de Lambda Layers
cdk deploy medical-analytics-layers-dev

# 2. Desplegar el stack de almacenamiento
cdk deploy medical-analytics-storage-dev

# 3. Desplegar el stack de ingesta
cdk deploy medical-analytics-ingestion-dev

# 4. Desplegar el stack de CDN
cdk deploy medical-analytics-cdn-dev
```

## 4. Obtener la API Key generada

Después del despliegue, es necesario obtener la API Key generada por API Gateway:

```bash
# Obtener la API key generada
aws apigateway get-api-keys --name-query medical-analytics-api-key --include-values --query 'items[0].value' --output text
```

## 5. Verificación del Despliegue

Después de completar los pasos anteriores, verifica que todo funciona correctamente:

```bash
# Obtener la URL de CloudFront
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-cdn-dev --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)
echo "URL del frontend: $CLOUDFRONT_URL"

# Verificar que los buckets S3 existen
aws s3 ls

# Comprobar que las funciones Lambda se han desplegado
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'medical-analytics-')]"
```

## 6. Prueba de Funcionalidad

1. Accede a la URL de CloudFront en un navegador
2. Crea un archivo Excel con las columnas requeridas:
   - NUMDOC_PACIENTE
   - FECHA_FOLIO
   - NOMBRE_PACIENTE
   - DIAGNÓSTICO
3. Sube el archivo a través de la interfaz web
4. Verifica que el archivo se haya almacenado correctamente:
   ```bash
   BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name medical-analytics-storage-dev --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" --output text)
   aws s3 ls s3://$BUCKET_NAME/raw/excel/ --recursive
   ```

## 7. Solución de Problemas Comunes

### Error "403 Forbidden" con CloudFront

Si recibes un error 403 al acceder a CloudFront:

```bash
# Ejecutar el script de corrección de permisos
./scripts/fix_cloudfront.sh
```

### Problemas con CORS

Si encuentras errores de CORS al subir archivos:
1. Asegúrate de estar accediendo a través de la URL de CloudFront, no directamente al bucket S3
2. Verifica que las cabeceras CORS estén correctamente configuradas en API Gateway

## 8. Limpieza de Recursos

Cuando ya no necesites la aplicación:

```bash
# Eliminar todos los stacks en orden inverso
cdk destroy medical-analytics-cdn-dev
cdk destroy medical-analytics-ingestion-dev
cdk destroy medical-analytics-storage-dev
cdk destroy medical-analytics-layers-dev

# O eliminar todos de una vez
cdk destroy --all
```

## Siguientes Pasos

Una vez completado el despliegue inicial, los siguientes pasos del proyecto serían:

1. Implementar la capa de procesamiento ETL con AWS Glue (Fase 3)
2. Implementar la capa de análisis y visualización (Fase 4)
3. Implementar monitoreo y seguridad avanzados (Fase 5)
4. Completar la documentación y pruebas (Fase 6)
