# Instrucciones para desplegar el Sistema de Analítica Médica

## Pasos simplificados

1. Primero, asegúrate de que tu entorno virtual de Python está activado:
   ```bash
   source venv/bin/activate
   ```

2. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

3. Asigna permisos de ejecución a los scripts:
   ```bash
   chmod +x fix_fresh.sh
   ./fix_fresh.sh
   ```

4. Ejecuta el script de despliegue:
   ```bash
   ./deploy_fresh.sh
   ```

5. Espera a que CloudFront se propague (puede tomar 15-30 minutos)

6. Accede al frontend mediante la URL de CloudFront proporcionada al final del despliegue

7. Si recibes un error 403 Forbidden al acceder a CloudFront, ejecuta el script de corrección de permisos:
   ```bash
   chmod +x fix_cloudfront.sh
   ./fix_cloudfront.sh
   ```

## Solución de problemas

### 1. Error "El bucket ya existe"

Si ves un error indicando que el bucket S3 ya existe, tienes dos opciones:
- Responder "s" cuando el script te pregunte si quieres eliminarlo
- Modificar el nombre del bucket en el código (storage_stack.py o cdn_stack.py)

### 2. Error "Dependencia cíclica"

Este error ha sido resuelto con la nueva arquitectura. Si lo sigues viendo, asegúrate de estar usando los archivos más recientes.

### 3. Error "There is already a Construct with name X"

Este error ha sido corregido. Si lo encuentras de nuevo, revisa los nombres de los constructos en los stacks.

### 4. CloudFront no está disponible inmediatamente

Es normal que la distribución de CloudFront tarde hasta 30 minutos en estar completamente disponible tras el despliegue inicial.

## Probar la configuración CORS

Una vez desplegado el sistema, puedes verificar que CORS está correctamente configurado con:

```bash
./test_cors.py <URL_API>upload --api-key <API_KEY>
```

Reemplaza `<URL_API>` y `<API_KEY>` con los valores mostrados al final del despliegue.
