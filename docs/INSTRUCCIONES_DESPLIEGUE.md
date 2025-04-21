# Instrucciones para Despliegue Correcto

Este documento proporciona instrucciones detalladas para desplegar correctamente el sistema de analítica médica, evitando los problemas que se han encontrado anteriormente.

## Requisitos Previos

Asegúrate de tener instalado:

1. AWS CLI configurado con las credenciales adecuadas
2. Node.js y npm
3. AWS CDK instalado: `npm install -g aws-cdk`
4. Python 3.9 o superior
5. Virtualenv: `pip install virtualenv`

## Preparación del Entorno

1. Clona el repositorio (si aún no lo has hecho)
   ```bash
   git clone <url-del-repositorio>
   cd medical-analytics-cdk
   ```

2. Crea y activa un entorno virtual
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias
   ```bash
   pip install -r requirements.txt
   ```

4. Arranca la aplicación CDK (solo primera vez)
   ```bash
   cdk bootstrap
   ```

## Despliegue Optimizado

Para un despliegue correcto, sigue estos pasos en el orden exacto:

### 1. Despliegue de Lambda Layers

Primero despliega las capas Lambda que contienen las dependencias:

```bash
cdk deploy medical-analytics-layers-dev
```

### 2. Despliegue del Storage Stack

Despliega el stack de almacenamiento que incluye la clave KMS configurada correctamente:

```bash
cdk deploy medical-analytics-storage-dev
```

### 3. Despliegue del Stack de Ingesta

Despliega el stack de ingestión que incluye API Gateway:

```bash
cdk deploy medical-analytics-ingestion-dev
```

### 4. Obtener la URL de API Gateway y la API Key

Después de desplegar el stack de ingesta, necesitarás obtener la URL de API Gateway y la API Key para el frontend:

```bash
# Obtener la URL de API Gateway
export API_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
echo "API URL: $API_URL"

# Obtener la API Key
export API_KEY=$(aws apigateway get-api-keys --name-query medical-analytics-api-key --include-values --query 'items[0].value' --output text)
echo "API Key: $API_KEY"
```

### 5. Configurar Variables para el Frontend

Antes de desplegar el CDN stack, actualiza el archivo app.py para incluir la API Key:

```bash
# Actualizar app.py con la API Key
sed -i.bak "s|api_key_value = \"placeholder-api-key\"|api_key_value = \"$API_KEY\"|g" app.py
```

### 6. Despliegue del Stack CDN

Finalmente, despliega el stack de CDN que incluye el frontend:

```bash
cdk deploy medical-analytics-cdn-dev
```

## Verificación del Despliegue

### 1. Verificar URL de CloudFront

```bash
export CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-cdn-dev --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)
echo "Frontend URL: $CLOUDFRONT_URL"
```

### 2. Verificar Encabezados CORS y CSP

Puedes usar curl para verificar que los encabezados CORS y CSP están configurados correctamente:

```bash
curl -I $CLOUDFRONT_URL
```

### 3. Probar la Aplicación

Accede a la URL de CloudFront en tu navegador y verifica que puedes:
- Ver la interfaz correctamente
- Seleccionar y subir un archivo Excel
- Recibir confirmación de que el archivo fue procesado

## Solución de Problemas

### Si encuentras problemas de CORS

Si ves errores CORS en la consola del navegador:

1. Verifica que estés accediendo a través de la URL de CloudFront, no directamente a S3
2. Limpia la caché del navegador (Ctrl+F5 o Cmd+Shift+R)
3. Prueba en modo incógnito o en otro navegador

### Si encuentras problemas con la API Key

Si recibes errores 403 al intentar usar la API:

1. Verifica que la API Key se haya pasado correctamente al frontend
2. Verifica que la API Key esté asociada correctamente al plan de uso en API Gateway
3. Puedes verificar la API Key manualmente:
   ```bash
   curl -X OPTIONS -H "Origin: $CLOUDFRONT_URL" -H "x-api-key: $API_KEY" "$API_URL/upload"
   ```

### Si hay problemas con CloudFront

1. Verifica que la distribución esté completamente desplegada (estado "Deployed" en la consola)
2. Verifica que la política de bucket S3 permita acceso a CloudFront
3. Invalidar la caché de CloudFront si es necesario:
   ```bash
   aws cloudfront create-invalidation --distribution-id EBPFC2GQEWZC1 --paths "/*"
   ```

## Mantenimiento del Sistema

### Actualización de la Aplicación

Para actualizar componentes específicos:

```bash
# Actualizar solo el frontend
cdk deploy medical-analytics-cdn-dev

# Actualizar API Gateway y Lambda
cdk deploy medical-analytics-ingestion-dev
```

### Limpieza de Recursos

Para eliminar todos los recursos desplegados:

```bash
cdk destroy --all
```

Nota: La eliminación de algunos recursos (como buckets S3) puede requerir pasos adicionales si contienen datos.
