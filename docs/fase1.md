# Fase 1: Configuración de Proyecto y Capa de Almacenamiento

## Objetivo

Establecer la base del proyecto CDK e implementar la estructura de almacenamiento S3.

## Tareas Completadas

- [x] Inicialización del Proyecto CDK
- [x] Implementación de Estructura de Almacenamiento S3
- [x] Configuración de Roles IAM Base

## Detalles de Implementación

### 1. Estructura del Proyecto

Se ha configurado un proyecto CDK con la siguiente estructura:

```
medical-analytics-cdk/
│
├── app.py                   # Punto de entrada de la aplicación CDK
├── requirements.txt         # Dependencias del proyecto
├── medical_analytics/       # Módulo principal del proyecto
│   ├── __init__.py
│   └── storage_stack.py     # Stack para la capa de almacenamiento
├── tests/                   # Pruebas unitarias
│   ├── __init__.py
│   └── phase1_test.py       # Pruebas para la Fase 1
├── empty-folder/            # Carpeta utilizada para crear estructura en S3
└── docs/                    # Documentación del proyecto
    └── fase1.md             # Documentación de la Fase 1
```

### 2. Implementación del Stack de Almacenamiento

El stack de almacenamiento (`StorageStack`) implementa:

1. **Bucket S3 para datos médicos**:
   - Nombre: `medical-analytics-project-dev`
   - Versionado habilitado para recuperación de datos
   - Encriptación con AWS KMS para proteger datos sensibles
   - Bloqueo completo de acceso público
   - Políticas de ciclo de vida para mover versiones antiguas a almacenamiento más económico
   - Estructura de carpetas definida según los requisitos del proyecto

2. **Clave KMS para encriptación de datos**:
   - Alias: `medical-analytics-key`
   - Rotación automática de clave habilitada
   - Período de espera de 7 días para eliminación

3. **Roles IAM con permisos mínimos necesarios**:
   - Rol de ingesta: para funciones Lambda que cargarán datos
   - Rol ETL: para trabajos de AWS Glue
   - Rol de análisis: para Athena y QuickSight

### 3. Estructura de Carpetas en S3

La estructura implementada sigue el patrón requerido:

```
s3://medical-analytics-project-dev/
├── raw/
│   ├── api/      # Datos de la API particionados por fecha
│   └── excel/    # Datos Excel particionados por fecha
├── cleaned/
│   ├── pacientes/      # Datos limpios particionados por FECHA_FOLIO
│   └── diagnosticos/   # Datos de diagnósticos
└── curated/
    ├── indicadores/
    │   ├── hta/        # Indicadores de hipertensión arterial
    │   └── dm/         # Indicadores de diabetes mellitus
    └── agregados/      # Datos agregados para reporting
```

### 4. Seguridad Implementada

- **Encriptación**:
  - Todos los datos en reposo están encriptados con AWS KMS
  - Encriptación SSL/TLS forzada para transferencias
  
- **Acceso**:
  - Roles IAM con principio de mínimo privilegio
  - Sin acceso público al bucket S3
  - Permisos separados por zona de datos y por función

- **Políticas de Ciclo de Vida**:
  - Retención de las 5 versiones más recientes
  - Transición a Infrequent Access después de 30 días
  - Transición a Glacier después de 90 días

### 5. Pruebas Implementadas

Se han implementado pruebas unitarias para verificar:
- Correcta creación del bucket S3 con todas sus propiedades
- Creación de la clave KMS con configuración apropiada
- Creación de roles IAM con los permisos adecuados
- Configuración correcta del ciclo de vida de objetos en S3

## Comandos para Desplegar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Sintetizar la aplicación CDK
cdk synth

# Desplegar los recursos
cdk deploy
```

## Siguientes Pasos

Después de desplegar esta fase, se puede proceder a la Fase 2 para implementar la capa de ingesta de datos, que incluirá:
- Componente de ingesta desde la API del cliente
- API Gateway para la carga de archivos Excel
- Frontend simple para carga de archivos
