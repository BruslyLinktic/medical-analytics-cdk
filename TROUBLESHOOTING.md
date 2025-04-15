# Solución de Problemas - Sistema de Analítica Médica

Este documento contiene soluciones para problemas comunes que puedes encontrar al configurar y ejecutar el proyecto.

## Problemas con la importación de módulos AWS CDK

### Error: "No module named 'aws_cdk_lib'"

**Síntoma**: Al importar `aws_cdk_lib` recibes un error de que no existe tal módulo.

**Solución**:
Este es un error común debido a la forma en que se nombra e importa AWS CDK. 

1. La forma correcta de importar es:
   ```python
   # Correcto
   from aws_cdk import Stack, Duration
   import aws_cdk as cdk

   # Incorrecto
   import aws_cdk_lib  # Este módulo no existe
   ```

2. Para solucionar problemas de importación, ejecuta:
   ```bash
   ./fix_cdk.sh
   ```
   
3. Si aún tienes problemas, verifica que el nombre del paquete es `aws-cdk-lib` (con guiones) en `requirements.txt`, pero se importa como `aws_cdk` (con guiones bajos) en el código.

### Error con módulos alpha como "aws_lambda_python_alpha"

**Síntoma**: No se puede importar o usar el módulo `aws_lambda_python_alpha`.

**Solución**:
1. Asegúrate de que el paquete alpha esté instalado correctamente:
   ```bash
   pip install aws-cdk.aws-lambda-python-alpha==2.119.0a0
   ```

2. En tu código, puedes importarlo de dos formas válidas:
   ```python
   # Opción 1
   from aws_cdk import aws_lambda_python_alpha
   
   # Opción 2
   import aws_cdk.aws_lambda_python_alpha
   ```

3. Si sigues teniendo problemas, verifica que la versión coincida con la de aws-cdk-lib:
   ```bash
   pip show aws-cdk-lib aws-cdk.aws-lambda-python-alpha
   ```

## Problemas con Python

### Error: "command not found: python"

**Síntoma**: El sistema no reconoce el comando `python`.

**Solución**:
1. En macOS y algunos sistemas Linux, usa `python3` en su lugar:
   ```bash
   python3 -m venv venv
   ```

2. Alternativamente, crea un alias en tu shell:
   ```bash
   echo "alias python=python3" >> ~/.zshrc  # o ~/.bashrc si usas bash
   source ~/.zshrc  # o ~/.bashrc
   ```

## Problemas con CDK

### Error: "No credentials available in {credentials file}"

**Síntoma**: CDK no puede acceder a las credenciales de AWS.

**Solución**:
1. Configura tus credenciales AWS:
   ```bash
   aws configure
   ```

2. O establece las variables de entorno:
   ```bash
   export AWS_ACCESS_KEY_ID=tu_access_key_id
   export AWS_SECRET_ACCESS_KEY=tu_secret_access_key
   export AWS_DEFAULT_REGION=tu_region
   ```

### Error: "Target of stack doesn't exist"

**Síntoma**: Al intentar sintetizar o desplegar, CDK no encuentra el stack.

**Solución**:
1. Asegúrate de estar en el directorio raíz del proyecto:
   ```bash
   cd /ruta/a/medical-analytics-cdk
   ```

2. Verifica que los nombres de los stacks en tu comando coincidan con los definidos en `app.py`:
   ```bash
   # Lista todos los stacks disponibles
   cdk list
   ```

3. Luego, usa el nombre exacto para sintetizar o desplegar:
   ```bash
   cdk synth medical-analytics-storage-dev
   ```

## Reinicio Completo

Si nada funciona, puedes intentar un reinicio completo:

1. Elimina el entorno virtual:
   ```bash
   rm -rf venv
   ```

2. Elimina cualquier caché de paquetes:
   ```bash
   rm -rf ~/.cache/pip
   ```

3. Reinicia el proceso de configuración:
   ```bash
   ./setup_env.sh
   source venv/bin/activate
   ```

Para más información o si continúas con problemas, consulta la documentación oficial de AWS CDK o abre un issue en el repositorio del proyecto.
