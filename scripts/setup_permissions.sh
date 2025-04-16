#!/bin/bash

# Script para configurar permisos de ejecución para los scripts
echo "Configurando permisos de ejecución para los scripts..."

chmod +x deploy_simplified.py
chmod +x test_cors.py

echo "¡Permisos configurados correctamente!"
echo ""
echo "Para desplegar el proyecto, ejecute:"
echo "./deploy_simplified.py"
echo ""
echo "Para probar CORS después del despliegue, ejecute:"
echo "./test_cors.py <URL_API> --api-key <API_KEY>"
