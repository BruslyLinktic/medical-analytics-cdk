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

- Python >= 3.9 (recomendado 3.9+)
- AWS CDK >= 2.119.0
- AWS CLI configurado con permisos adecuados
- Node.js >= 14 (requerido por CDK)

## Instalación rápida

```bash
# Asegúrate de tener instalado Python 3.9+ y Git

# Dar permisos al script de instalación y ejecutarlo
chmod +x setup_env.sh
./setup_env.sh

# Activar el entorno virtual
source venv/bin/activate
```

## Instalación manual

```bash
# Crear entorno virtual (Si python3 no funciona, prueba con python)
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

## Solución de problemas

Si encuentras problemas durante la instalación o ejecución:

```bash
# Verificar y corregir dependencias (si tienes problemas con módulos)
./fix_dependencies.sh

# Probar si el proyecto compila correctamente
./test_synth.sh
```

Consulta el archivo [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) para soluciones detalladas a problemas comunes.

## Despliegue

```bash
# Verificar que el entorno virtual esté activado (venv)

# Sintetizar la aplicación CDK
cdk synth

# Desplegar un stack específico (recomendado para la primera vez)
cdk deploy medical-analytics-storage-dev

# O desplegar todos los stacks
cdk deploy --all
```

## Documentación

Consulta la carpeta `docs/` para más detalles sobre la arquitectura y funcionamiento del sistema.
