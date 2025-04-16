#!/bin/bash
# Script para desplegar el sistema de analítica médica con correcciones a problemas CORS y CloudFront

set -e  # Detener ejecución si algún comando falla

echo "======================================================="
echo "  DESPLIEGUE DEL SISTEMA DE ANALÍTICA MÉDICA"
echo "======================================================="

# Verificar activación del entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo "⚠️  El entorno virtual no está activado."
  echo "   Por favor, actívelo con: source venv/bin/activate"
  exit 1
fi

# Verificar existencia de bucket S3
if aws s3 ls | grep -q "medical-analytics-project-dev"; then
  echo "⚠️  El bucket 'medical-analytics-project-dev' ya existe."
  read -p "¿Desea eliminarlo y crear uno nuevo? (s/n): " choice
  if [[ "$choice" == "s" || "$choice" == "S" ]]; then
    echo "Eliminando bucket existente..."
    aws s3 rb s3://medical-analytics-project-dev --force
  else
    echo "Debe modificar el nombre del bucket en storage_stack.py antes de continuar."
    exit 1
  fi
fi

# Sintetizar el proyecto para verificar que está correcto
echo ""
echo "Sintetizando el proyecto para verificar que no hay errores..."
cdk synth || {
  echo "❌ Error al sintetizar el proyecto. Corrija los errores antes de continuar."
  exit 1
}

# Desplegar los stacks en orden
echo ""
echo "Desplegando stack de almacenamiento..."
cdk deploy medical-analytics-storage-dev --require-approval never

echo ""
echo "Desplegando stack de ingesta..."
cdk deploy medical-analytics-ingestion-dev --require-approval never

echo ""
echo "Desplegando stack de CDN..."
cdk deploy medical-analytics-cdn-dev --require-approval never

# Obtener información de salida
echo ""
echo "Obteniendo información de recursos desplegados..."
API_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
API_KEY=$(aws cloudformation describe-stacks --stack-name medical-analytics-ingestion-dev --query "Stacks[0].Outputs[?OutputKey=='ApiKeyValue'].OutputValue" --output text)
CF_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-cdn-dev --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)

# Mostrar información de salida
echo ""
echo "======================================================="
echo "  DESPLIEGUE COMPLETADO CON ÉXITO"
echo "======================================================="
echo ""
echo "Recursos disponibles:"
echo "- API Gateway: $API_URL"
echo "- API Key: $API_KEY"
echo "- Frontend (CloudFront): $CF_URL"
echo ""
echo "⚠️  IMPORTANTE:"
echo "1. La distribución de CloudFront puede tardar hasta 15-30 minutos en propagarse completamente."
echo "2. Utiliza la URL de CloudFront para acceder al frontend."
echo "3. La API Key ya está configurada en el frontend automáticamente."
echo ""
echo "Para probar la configuración CORS después del despliegue, puedes ejecutar:"
echo "./test_cors.py ${API_URL}upload --api-key $API_KEY"
echo ""
echo "======================================================="
