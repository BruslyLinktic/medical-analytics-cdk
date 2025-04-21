#!/bin/bash

# Script para corregir problemas de KMS y CSP en la implementación de Medical Analytics

# Colores para mejor legibilidad
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

echo -e "${BLUE}=== Corrección de Problemas Medical Analytics ===${NC}"
echo

# Verificar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Error: Python 3 no está instalado${NC}"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo -e "${RED}Error: pip3 no está instalado${NC}"; exit 1; }

# Verificar boto3
pip3 list | grep boto3 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Instalando boto3...${NC}"
    pip3 install boto3
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: No se pudo instalar boto3${NC}"
        exit 1
    fi
fi

# Verificar credenciales de AWS
echo -e "${YELLOW}Verificando credenciales de AWS...${NC}"
python3 -c "import boto3; boto3.client('sts').get_caller_identity()" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: No se pueden validar las credenciales de AWS${NC}"
    echo -e "${YELLOW}Por favor, ejecuta 'aws configure' para configurar tus credenciales${NC}"
    exit 1
fi
echo -e "${GREEN}Credenciales de AWS verificadas correctamente${NC}"

# Dar permisos de ejecución a los scripts de Python
chmod +x "$(dirname "$0")/fix_csp_direct.py"
chmod +x "$(dirname "$0")/fix_kms_direct.py"

# Ejecutar script de corrección de KMS
echo -e "${BLUE}\n=== Corrigiendo políticas KMS ===${NC}"
python3 "$(dirname "$0")/fix_kms_direct.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al corregir las políticas KMS${NC}"
    # Continuar de todas formas, ya que el problema de CSP es independiente
    echo -e "${YELLOW}Continuando con la corrección de CSP...${NC}"
fi

# Ejecutar script de corrección de CSP
echo -e "${BLUE}\n=== Corrigiendo políticas CSP de CloudFront ===${NC}"
python3 "$(dirname "$0")/fix_csp_direct.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al corregir las políticas CSP${NC}"
    echo -e "${YELLOW}Por favor, revisa los mensajes de error arriba para más detalles${NC}"
    exit 1
fi

echo -e "${GREEN}\n=== ¡Correcciones completadas con éxito! ===${NC}"
echo -e "${YELLOW}IMPORTANTE: Los cambios en CloudFront pueden tardar hasta 15 minutos en propagarse completamente.${NC}"
echo -e "${YELLOW}Si los problemas persisten después de 15 minutos, limpia la caché de tu navegador.${NC}"
echo
echo -e "${BLUE}Para verificar el estado de CloudFront:${NC}"
echo "  1. Visita la consola de AWS: https://console.aws.amazon.com/cloudfront/"
echo "  2. Selecciona la distribución EBPFC2GQEWZC1"
echo "  3. Verifica que el estado sea 'Deployed'"
echo
