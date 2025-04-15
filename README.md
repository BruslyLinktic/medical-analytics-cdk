# Sistema de Analítica Médica con AWS CDK

Este proyecto implementa un sistema de analítica para datos médicos recolectados en campañas de salud, usando una arquitectura serverless implementada como código usando AWS CDK con Python.

## Estructura del Proyecto

El proyecto está organizado por fases:

1. **Fase 1**: Configuración de proyecto y capa de almacenamiento
2. **Fase 2**: Implementación de la capa de ingesta de datos
3. **Fase 3**: Implementación de la capa de procesamiento ETL
4. **Fase 4**: Implementación de la capa de análisis y visualización
5. **Fase 5**: Implementación de monitoreo y seguridad
6. **Fase 6**: Documentación, pruebas y despliegue

## Requisitos

- Python >= 3.8
- AWS CDK >= 2.0
- AWS CLI configurado con permisos adecuados

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/BruslyLinktic/medical-analytics-cdk.git
cd medical-analytics-cdk

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Despliegue

```bash
# Sintetizar la aplicación CDK
cdk synth

# Desplegar los recursos
cdk deploy
```

## Documentación

Consulta la carpeta `docs/` para más detalles sobre la arquitectura y funcionamiento del sistema.
