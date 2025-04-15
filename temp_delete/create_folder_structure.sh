#!/bin/bash

# Script para crear la estructura de carpetas en el bucket S3 usando AWS CLI
# Este script debe ejecutarse después de que el stack haya sido desplegado

# Definir el nombre del bucket (actualizar según sea necesario)
BUCKET_NAME="medical-analytics-project-dev"

# Definir la estructura de carpetas requerida
FOLDERS=(
    "raw/api/"
    "raw/excel/"
    "cleaned/pacientes/"
    "cleaned/diagnosticos/"
    "curated/indicadores/hta/"
    "curated/indicadores/dm/"
    "curated/agregados/"
)

echo "Creando estructura de carpetas en el bucket $BUCKET_NAME..."

# Crear cada carpeta usando AWS CLI
for folder in "${FOLDERS[@]}"; do
    echo "Creando carp