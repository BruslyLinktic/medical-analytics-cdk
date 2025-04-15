#!/bin/bash

# Detectar qué versión de Python está disponible
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: No se encontró Python. Por favor instala Python 3."
    exit 1
fi

# Crear entorno virtual
$PYTHON_CMD -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Asegurarnos de que el paquete alpha esté instalado correctamente
pip install aws-cdk.aws-lambda-python-alpha==2.119.0a0

# Instalar paquetes opcionales que podrían ser útiles
pip install pylint pytest-cov black

echo "Entorno virtual configurado correctamente."
echo "Para activar el entorno virtual, ejecuta: source venv/bin/activate"
