#!/bin/bash

# Script para hacer ejecutables todos los scripts del proyecto

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Haciendo ejecutables los scripts del proyecto...${NC}"

# Scripts en la raíz del proyecto
chmod +x fix_cloudfront.sh
chmod +x apply_cdn_fix.sh
chmod +x deploy.py
chmod +x deploy_corrected.sh
chmod +x deploy_fresh.sh
chmod +x deploy_simplified.py
chmod +x fix_fresh.sh
chmod +x fix_permissions.sh
chmod +x setup_permissions.sh
chmod +x test_cors.py
chmod +x make_scripts_executable.sh

# Scripts en la carpeta "scripts"
chmod +x scripts/fix_cloudfront_permissions.py

echo -e "${GREEN}¡Scripts ahora son ejecutables!${NC}"
echo -e "${YELLOW}Para resolver el problema de CloudFront, puedes ejecutar:${NC}"
echo -e "  ${GREEN}./fix_cloudfront.sh${NC} - Para corregir los permisos directamente en AWS"
echo -e "  ${GREEN}./apply_cdn_fix.sh${NC} - Para aplicar la corrección al código CDK y redesplegar"
