# Solución de Problemas - Sistema de Analítica Médica

Este documento contiene soluciones para problemas comunes que puedes encontrar al configurar y ejecutar el proyecto.

## Problemas con CloudFront y S3

### Error: "403 Forbidden" al acceder a la interfaz web a través de CloudFront

**Síntoma**: Al intentar acceder a la URL de CloudFront, recibes un error 403 Forbidden (AccessDenied).

**Solución**:
Este error generalmente ocurre porque CloudFront no tiene los permisos adecuados para acceder a los objetos del bucket S3.

1. Ejecuta el script de corrección de permisos:
   ```bash
   ./fix_cloudfront.sh
   ```

2. Este script realizará las siguientes acciones:
   - Identifica la distribución de CloudFront relacionada con el proyecto
   - Obtiene el OAI (Origin Access Identity) configurado
   - Actualiza la política del bucket S3 para permitir acceso explícito a CloudFront
   - Configura correctamente CORS para el bucket

3. Si el script no resuelve el problema, verifica manualmente:
   - Que el OAI esté correctamente configurado en CloudFront
   - Que la política del bucket permita acceso al OAI
   - Que los objetos del bucket no tengan ACLs restrictivas

4. En caso de problemas persistentes, puedes reiniciar el proceso completo:
   ```bash
   cdk destroy medical-analytics-cdn-dev
   cdk deploy medical-analytics-cdn-dev
   ```

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
