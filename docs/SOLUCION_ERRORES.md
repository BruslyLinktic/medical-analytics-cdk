# Solución de Errores de KMS y Content Security Policy (CSP)

Este documento explica los errores que estabas experimentando con tu aplicación de analítica médica y proporciona instrucciones para resolverlos.

## Problemas detectados

Hay dos problemas principales:

1. **Problema con la clave KMS**: La clave KMS creada no tiene permisos adecuados para que CloudFront pueda acceder a los recursos encriptados.
2. **Problema de Content Security Policy (CSP)**: La política de seguridad de contenido de CloudFront está bloqueando scripts y estilos inline en tu frontend.

## Solución

### Opción 1: Corregir la configuración existente (sin redespliegue)

Puedes utilizar el script de corrección para actualizar la configuración existente sin tener que redesplegar todo:

```bash
# Instalar boto3 si no está instalado
pip install boto3

# Dar permisos de ejecución al script
chmod +x scripts/fix_deployment.py

# Ejecutar el script
python scripts/fix_deployment.py
```

El script realiza las siguientes acciones:
1. Busca la clave KMS asociada a tu proyecto y actualiza sus políticas para permitir que CloudFront acceda a los recursos encriptados.
2. Encuentra la distribución de CloudFront y crea una nueva política de encabezados que permite scripts y estilos inline.

**IMPORTANTE**: Los cambios en CloudFront pueden tardar hasta 15 minutos en propagarse completamente. Si después de este tiempo sigues viendo errores, intenta limpiar la caché de tu navegador.

### Opción 2: Modificaciones en el código CDK y redespliegue

Se han realizado cambios en dos archivos principales:

1. **cdn_stack.py**: Se ha actualizado la política CSP para permitir scripts y estilos inline agregando el valor `'unsafe-inline'`.
2. **storage_stack.py**: Se ha agregado una política explícita a la clave KMS para permitir que CloudFront pueda usar la clave.

Para aplicar estos cambios, puedes redesplegar el stack:

```bash
# Redesplegar el stack de CDN
cdk deploy medical-analytics-cdn-dev
```

## Entendiendo los errores

### Error de Content Security Policy (CSP)

Los errores que estabas viendo eran:

```
Refused to apply inline style because it violates the following Content Security Policy directive: "style-src 'self' https://cdn.jsdelivr.net". Either the 'unsafe-inline' keyword, a hash ('sha256-...'), or a nonce ('nonce-...') is required to enable inline execution.
```

Esto ocurre porque tu HTML contiene estilos y scripts inline, pero la política CSP estaba configurada para bloquearlos. Al agregar `'unsafe-inline'` a las directivas `script-src` y `style-src`, permitimos estos recursos inline.

### Error de KMS

El problema con KMS se debía a que la clave utilizada para encriptar los recursos no estaba configurada para permitir que CloudFront accediera a ellos. Al agregar una política explícita para CloudFront, solucionamos este problema.

## ¿Por qué funcionan estas soluciones?

- **Para el problema de CSP**: Al agregar `'unsafe-inline'` a las directivas, le decimos al navegador que está bien ejecutar código JavaScript y aplicar estilos que están escritos directamente en el HTML, en lugar de en archivos externos.

- **Para el problema de KMS**: Al modificar la política de la clave KMS, permitimos que CloudFront pueda descifrar los recursos encriptados cuando los sirve a los usuarios. Esto se hace añadiendo un "statement" en la política que otorga los permisos `kms:Decrypt`, `kms:Encrypt` y `kms:GenerateDataKey` al servicio de CloudFront.

## Recomendaciones a futuro

1. **Mejorar la seguridad de CSP**: Aunque `'unsafe-inline'` resuelve el problema, es mejor a largo plazo:
   - Mover todos los estilos a archivos CSS externos
   - Mover código JavaScript a archivos externos
   - Utilizar hashes o nonces para scripts y estilos que deben ser inline

2. **Gestión de claves KMS**: Considera documentar y revisar periódicamente tus políticas de KMS para evitar problemas de acceso. Es una buena práctica seguir el principio de menor privilegio.

3. **Pruebas antes de producción**: Configura un entorno de pruebas que refleje exactamente tu entorno de producción para detectar estos problemas antes de lanzar a producción.
