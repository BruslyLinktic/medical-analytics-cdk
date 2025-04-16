#!/bin/bash
# Script para dar permisos de ejecución al script de despliegue fresco

chmod +x deploy_fresh.sh
chmod +x test_cors.py

# Asegurarnos de que los módulos de CDK estén instalados
npm list -g aws-cdk &> /dev/null || echo "⚠️ CDK no detectado. Instale con: npm install -g aws-cdk"

# Verificar si tenemos el bucket S3
aws s3 ls s3://medical-analytics-frontend-dev 2>&1 > /dev/null
if [ $? -eq 0 ]; then
  echo "🗑️ Limpiando bucket de frontend existente..."
  aws s3 rm s3://medical-analytics-frontend-dev --recursive
fi

aws s3 ls s3://medical-analytics-project-dev 2>&1 > /dev/null
if [ $? -eq 0 ]; then
  echo "🗑️ Limpiando bucket de proyecto existente..."
  aws s3 rm s3://medical-analytics-project-dev --recursive
fi

echo "=================================================="
echo "  PERMISOS CONFIGURADOS"
echo "=================================================="
echo ""
echo "1. Ahora puedes ejecutar ./deploy_fresh.sh para desplegar el proyecto"
echo "2. Este enfoque elimina completamente las dependencias cíclicas"
echo "3. Toda la lógica del frontend ahora está contenida en el CDN stack"
echo ""
echo "Este es el enfoque recomendado para desplegar tu proyecto"
echo "=================================================="
