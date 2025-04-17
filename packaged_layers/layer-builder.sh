#!/bin/bash

# Script para construir las Lambda Layers manualmente sin depender de Docker

# Colores para salida
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando construcción de Lambda Layers...${NC}"

# Directorio base del proyecto
PROJECT_DIR="/Users/brandowleon/medical-analytics-cdk"

# Definir las capas a construir
LAYERS=("pandas_layer" "common_layer")

# Crear directorio para almacenar las capas empaquetadas si no existe
mkdir -p ${PROJECT_DIR}/packaged_layers

for LAYER in "${LAYERS[@]}"; do
    echo -e "${GREEN}Construyendo capa: ${LAYER}${NC}"
    
    # Crear estructura temporal
    TEMP_DIR=${PROJECT_DIR}/packaged_layers/${LAYER}
    mkdir -p ${TEMP_DIR}/python
    
    # Copiar requirements.txt
    cp ${PROJECT_DIR}/layers/${LAYER}/requirements.txt ${TEMP_DIR}/
    
    # Instalar dependencias en el directorio python
    cd ${TEMP_DIR}
    pip install -r requirements.txt -t python/
    
    # Crear archivo ZIP
    zip -r ${PROJECT_DIR}/packaged_layers/${LAYER}.zip python/
    
    echo -e "${GREEN}✅ Capa ${LAYER} construida exitosamente en: ${PROJECT_DIR}/packaged_layers/${LAYER}.zip${NC}"
done

echo -e "${GREEN}Todas las capas han sido construidas exitosamente.${NC}"
