#!/bin/bash

# Script para construir las capas sin Docker y desplegar el proyecto

# Colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando construcción de capas y despliegue ===${NC}"

# 1. Preparación del entorno
echo -e "${YELLOW}Activando entorno virtual...${NC}"
source venv/bin/activate


# 5. Desplegar los stacks
echo -e "${YELLOW}Desplegando stacks...${NC}"
cdk bootstrap || {
    echo -e "${RED}Error durante el bootstrap.${NC}"
    echo -e "${YELLOW}Intentando continuar con el despliegue...${NC}"
}

cdk deploy --all || {
    echo -e "${RED}Error durante el despliegue.${NC}"
    exit 1
}

# 6. Mostrar información después del despliegue
echo -e "${GREEN}=== Despliegue completado exitosamente ===${NC}"

echo -e "${YELLOW}Obteniendo URL de CloudFront...${NC}"
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name medical-analytics-cdn-dev --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)
echo -e "${GREEN}URL del frontend: ${BLUE}$CLOUDFRONT_URL${NC}"

echo -e "${YELLOW}Para obtener la API key, ejecuta:${NC}"
echo -e "${BLUE}aws apigateway get-api-keys --name-query medical-analytics-api-key --include-values --query 'items[0].value' --output text${NC}"

exit 0
