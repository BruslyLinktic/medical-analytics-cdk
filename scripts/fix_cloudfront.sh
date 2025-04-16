#!/bin/bash

# Script para corregir permisos entre CloudFront y S3
# Este script hace ejecutable el script Python y lo ejecuta

# Colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando corrección de permisos de CloudFront...${NC}"

# Hacer ejecutable el script Python
chmod +x scripts/fix_cloudfront_permissions.py

# Verificar si el entorno virtual existe y activarlo
if [ -d "venv" ]; then
    echo -e "${GREEN}Activando entorno virtual...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}No se encontró el entorno virtual. Creando uno nuevo...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    # Instalar dependencias
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    pip install boto3
fi

# Ejecutar el script Python
echo -e "${GREEN}Ejecutando script de corrección de permisos...${NC}"
python scripts/fix_cloudfront_permissions.py

# Verificar si el script se ejecutó correctamente
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Permisos corregidos exitosamente!${NC}"
    echo -e "${YELLOW}Ahora puedes acceder a tu interfaz web a través de CloudFront.${NC}"
    echo -e "${YELLOW}La URL de CloudFront se puede encontrar en la consola de AWS o usando:${NC}"
    echo -e "aws cloudfront list-distributions --query \"DistributionList.Items[?contains(Comment, 'medical-analytics')].DomainName\" --output text"
else
    echo -e "${RED}Error al corregir los permisos. Revisa los mensajes de error anteriores.${NC}"
fi

# Desactivar entorno virtual
deactivate

echo -e "${GREEN}¡Proceso completado!${NC}"
