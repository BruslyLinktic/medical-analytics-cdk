#!/bin/bash

# Script para desplegar la aplicación de Analítica Médica
# Este script maneja el despliegue y la configuración posterior

# Colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando despliegue del Sistema de Analítica Médica ===${NC}"

# Función para mostrar ayuda
function show_help {
  echo -e "${YELLOW}Uso: $0 [opciones]${NC}"
  echo -e "Opciones:"
  echo -e "  -h, --help            Mostrar esta ayuda"
  echo -e "  -s, --stage STAGE     Ambiente de despliegue (dev, test, prod) [default: dev]"
  echo -e "  -a, --all             Desplegar todos los stacks (por defecto)"
  echo -e "  --storage             Desplegar solo el stack de almacenamiento"
  echo -e "  --ingestion           Desplegar solo el stack de ingesta"
  echo -e "  --cdn                 Desplegar solo el stack de CDN"
  echo -e "  --skip-bootstrap      Omitir el bootstrap de CDK"
}

# Valores por defecto
STAGE="dev"
DEPLOY_STORAGE=true
DEPLOY_INGESTION=true
DEPLOY_CDN=true
SKIP_BOOTSTRAP=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -s|--stage)
      STAGE="$2"
      shift 2
      ;;
    -a|--all)
      DEPLOY_STORAGE=true
      DEPLOY_INGESTION=true
      DEPLOY_CDN=true
      shift
      ;;
    --storage)
      DEPLOY_STORAGE=true
      DEPLOY_INGESTION=false
      DEPLOY_CDN=false
      shift
      ;;
    --ingestion)
      DEPLOY_STORAGE=false
      DEPLOY_INGESTION=true
      DEPLOY_CDN=false
      shift
      ;;
    --cdn)
      DEPLOY_STORAGE=false
      DEPLOY_INGESTION=false
      DEPLOY_CDN=true
      shift
      ;;
    --skip-bootstrap)
      SKIP_BOOTSTRAP=true
      shift
      ;;
    *)
      echo -e "${RED}Error: Opción desconocida: $1${NC}"
      show_help
      exit 1
      ;;
  esac
done

# Verificar entorno virtual
if [ ! -d "venv" ]; then
  echo -e "${YELLOW}No se encontró el entorno virtual. Creando uno nuevo...${NC}"
  python3 -m venv venv
fi

# Activar entorno virtual
echo -e "${GREEN}Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${GREEN}Instalando dependencias...${NC}"
pip install -r requirements.txt

# Bootstrap CDK (si no se omite)
if [ "$SKIP_BOOTSTRAP" = false ]; then
  echo -e "${GREEN}Ejecutando bootstrap de CDK...${NC}"
  cdk bootstrap
else
  echo -e "${YELLOW}Omitiendo bootstrap de CDK...${NC}"
fi

# Función para desplegar un stack y verificar éxito
function deploy_stack {
  local stack_name=$1
  local stack_id=$2
  
  echo -e "${BLUE}=== Desplegando $stack_name ===${NC}"
  cdk deploy $stack_id --require-approval never
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}$stack_name desplegado exitosamente.${NC}"
    return 0
  else
    echo -e "${RED}Error al desplegar $stack_name.${NC}"
    return 1
  fi
}

# Desplegar stacks según configuración
STACK_PREFIX="medical-analytics"
SUCCESS=true

if [ "$DEPLOY_STORAGE" = true ]; then
  deploy_stack "Stack de Almacenamiento" "${STACK_PREFIX}-storage-${STAGE}"
  if [ $? -ne 0 ]; then SUCCESS=false; fi
fi

if [ "$DEPLOY_INGESTION" = true ] && [ "$SUCCESS" = true ]; then
  deploy_stack "Stack de Ingesta" "${STACK_PREFIX}-ingestion-${STAGE}"
  if [ $? -ne 0 ]; then SUCCESS=false; fi
fi

if [ "$DEPLOY_CDN" = true ] && [ "$SUCCESS" = true ]; then
  deploy_stack "Stack de CDN" "${STACK_PREFIX}-cdn-${STAGE}"
  if [ $? -ne 0 ]; then SUCCESS=false; fi
  
  # Corregir permisos de CloudFront
  if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Ejecutando script de corrección de permisos de CloudFront...${NC}"
    python scripts/fix_cloudfront_permissions.py
  fi
fi

# Mostrar resultado final
if [ "$SUCCESS" = true ]; then
  echo -e "${GREEN}=== Despliegue completado exitosamente ===${NC}"
  
  # Recuperar URL de CloudFront
  if [ "$DEPLOY_CDN" = true ]; then
    echo -e "${BLUE}Obteniendo URL de CloudFront...${NC}"
    CF_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}-cdn-${STAGE} --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)
    echo -e "${GREEN}URL de la aplicación: ${BLUE}$CF_URL${NC}"
  fi
  
  # Verificar si se necesita configurar la API key
  if [ "$DEPLOY_INGESTION" = true ]; then
    echo -e "${YELLOW}Para obtener la API key para el frontend, ejecute:${NC}"
    echo -e "aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}-ingestion-${STAGE} --query \"Stacks[0].Outputs[?OutputKey=='GetApiKeyCommand'].OutputValue\" --output text | bash"
  fi
else
  echo -e "${RED}=== Despliegue fallido ===${NC}"
  echo -e "${YELLOW}Por favor revise los mensajes de error anteriores.${NC}"
fi

# Desactivar entorno virtual
deactivate

exit 0
