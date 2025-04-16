#!/bin/bash

# Script para aplicar la solución al problema de CloudFront-S3
# Este script reemplaza el archivo cdn_stack.py con la versión corregida

# Colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Aplicando solución al problema de CloudFront...${NC}"

# Verificar que los archivos existan
if [ ! -f "medical_analytics/cdn_stack/cdn_stack.py" ]; then
    echo -e "${RED}Error: No se encuentra el archivo cdn_stack.py${NC}"
    exit 1
fi

if [ ! -f "medical_analytics/cdn_stack/cdn_stack_fixed.py" ]; then
    echo -e "${RED}Error: No se encuentra el archivo cdn_stack_fixed.py${NC}"
    exit 1
fi

# Crear backup del archivo original
cp medical_analytics/cdn_stack/cdn_stack.py medical_analytics/cdn_stack/cdn_stack.py.bak
echo -e "${GREEN}Se ha creado un backup en medical_analytics/cdn_stack/cdn_stack.py.bak${NC}"

# Reemplazar con el archivo corregido
cp medical_analytics/cdn_stack/cdn_stack_fixed.py medical_analytics/cdn_stack/cdn_stack.py
echo -e "${GREEN}Se ha reemplazado el archivo cdn_stack.py con la versión corregida${NC}"

# Preguntar si desea redesplegar el stack
echo -e "${YELLOW}¿Deseas redesplegar el stack de CDN para aplicar los cambios? (s/n)${NC}"
read respuesta

if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
    echo -e "${YELLOW}Redesplegando el stack de CDN...${NC}"
    
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
        pip install -r requirements.txt
    fi
    
    # Redesplegar el stack de CDN
    echo -e "${YELLOW}Ejecutando 'cdk deploy medical-analytics-cdn-dev'...${NC}"
    cdk deploy medical-analytics-cdn-dev
    
    # Desactivar entorno virtual
    deactivate
    
    echo -e "${GREEN}Redespliegue completado. Los cambios deberían estar activos en unos minutos.${NC}"
else
    echo -e "${YELLOW}No se redesplegará el stack. Recuerda ejecutar 'cdk deploy medical-analytics-cdn-dev' para aplicar los cambios.${NC}"
fi

echo -e "${GREEN}¡Solución aplicada correctamente!${NC}"
echo -e "${YELLOW}Si persiste el problema, ejecuta './fix_cloudfront.sh' para ajustar los permisos directamente en AWS.${NC}"
