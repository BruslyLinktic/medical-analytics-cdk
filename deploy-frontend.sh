#!/bin/bash

# Script para desplegar el frontend con la URL de API actualizada

# Obtener la URL de la API desde CloudFormation
API_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)

if [ -z "$API_URL" ]; then
  echo "Error: No se pudo obtener la URL de la API. Asegúrate de que el stack ha sido desplegado correctamente."
  exit 1
fi

echo "URL de API encontrada: $API_URL"

# Crear una copia temporal del archivo HTML
cp frontend/index.html frontend/index.html.tmp

# Reemplazar el placeholder con la URL real
sed "s|{{API_ENDPOINT}}|$API_URL|g" frontend/index.html.tmp > frontend/index.html

echo "Archivo HTML actualizado con la URL de la API."

# Limpiar
rm frontend/index.html.tmp

# Obtener el nombre del bucket frontend
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Resources[?LogicalResourceId=='MedicalAnalyticsFrontendBucket'].PhysicalResourceId" --output text)

if [ -z "$BUCKET_NAME" ]; then
  echo "Error: No se pudo obtener el nombre del bucket. Usando nombre predeterminado."
  BUCKET_NAME="medical-analytics-frontend-dev"
fi

echo "Bucket encontrado: $BUCKET_NAME"

# Subir el archivo HTML actualizado al bucket
aws s3 cp frontend/index.html s3://$BUCKET_NAME/index.html

echo "Frontend actualizado y desplegado correctamente."
echo "Para acceder al frontend, visita: http://$BUCKET_NAME.s3-website-$(aws configure get region).amazonaws.com"
