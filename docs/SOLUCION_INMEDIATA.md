# Solución Inmediata para Problemas de CloudFront y KMS

Este documento proporciona instrucciones directas para solucionar los problemas de Content Security Policy (CSP) y KMS que estás experimentando con tu aplicación de analítica médica.

## Identificación de problemas

1. **Problema CSP en CloudFront**: Los errores que ves en el navegador indican que CloudFront está bloqueando estilos y scripts inline debido a restricciones de Content Security Policy.

   ```
   Refused to apply inline style because it violates the following Content Security Policy directive: "style-src 'self' https://cdn.jsdelivr.net". Either the 'unsafe-inline' keyword, a hash ('sha256-...'), or a nonce ('nonce-...') is required to enable inline execution.
   ```

2. **Problema de KMS**: La clave KMS que estás usando para encriptar datos no tiene los permisos adecuados para que CloudFront acceda a los recursos encriptados.

## Solución Rápida (Método Directo)

He creado scripts específicos para corregir estos problemas sin necesidad de redesplegar toda la infraestructura. Estos scripts modifican directamente los recursos existentes en AWS.

### Instrucciones para la solución rápida:

1. **Dar permisos de ejecución al script de solución:**

   ```bash
   chmod +x scripts/fix_all.sh
   ```

2. **Ejecutar el script de solución:**

   ```bash
   ./scripts/fix_all.sh
   ```

El script realizará las siguientes acciones:
- Verificará las dependencias necesarias
- Actualizará la política de KMS para permitir que CloudFront acceda a los recursos encriptados
- Actualizará la política CSP de CloudFront para permitir scripts y estilos inline
- Mostrará mensajes detallados de progreso y confirmación

**IMPORTANTE**: Los cambios en CloudFront pueden tardar hasta 15 minutos en propagarse completamente. Si después de este tiempo sigues viendo errores, intenta limpiar la caché de tu navegador.

## Solución Alternativa (Ejecutar scripts por separado)

Si prefieres ejecutar los scripts por separado:

1. **Para corregir solo el problema de CSP:**

   ```bash
   chmod +x scripts/fix_csp_direct.py
   python3 scripts/fix_csp_direct.py
   ```

2. **Para corregir solo el problema de KMS:**

   ```bash
   chmod +x scripts/fix_kms_direct.py
   python3 scripts/fix_kms_direct.py
   ```

## Verificación de la corrección

Después de ejecutar los scripts de corrección:

1. Espera al menos 15 minutos para que los cambios se propaguen
2. Limpia la caché de tu navegador (Ctrl+F5 o Cmd+Shift+R)
3. Intenta cargar nuevamente la aplicación: `https://d2fypua5bbhj7a.cloudfront.net/`

Si todo funciona correctamente, ya no deberías ver los errores de CSP en la consola del navegador.

## Solución a largo plazo (Para futuros despliegues)

Para evitar estos problemas en futuros despliegues, he modificado los archivos de infraestructura CDK:

1. **cdn_stack.py**: Se ha actualizado la política CSP para permitir scripts y estilos inline agregando el valor `'unsafe-inline'` a las directivas relevantes.

2. **storage_stack.py**: Se ha añadido una política explícita a la clave KMS para permitir que CloudFront pueda usar la clave.

Estas modificaciones ya están aplicadas en tu código, por lo que los futuros despliegues no deberían presentar estos problemas.

## Explicación detallada de los problemas

### ¿Por qué ocurre el problema de CSP?

La Content Security Policy (CSP) es un mecanismo de seguridad implementado por los navegadores web que ayuda a prevenir ataques de inyección de código (como XSS). CloudFront permite configurar una política CSP en las respuestas HTTP que envía a los navegadores.

En tu configuración original, la política CSP estaba configurada para permitir solo estilos y scripts desde fuentes específicas (el propio origen y cdn.jsdelivr.net), pero no permitía scripts ni estilos inline (es decir, escritos directamente en el HTML). Sin embargo, tu frontend utiliza estilos y scripts inline, lo que causaba que el navegador los bloqueara.

La directiva original era:
```
default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net;
```

La hemos modificado a:
```
default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
```

La adición de `'unsafe-inline'` permite que los estilos y scripts inline funcionen correctamente.

### ¿Por qué ocurre el problema de KMS?

AWS Key Management Service (KMS) utiliza políticas de acceso para controlar quién puede utilizar las claves de encriptación. Cuando configuras un servicio como CloudFront para trabajar con recursos encriptados por KMS, necesitas otorgar explícitamente permisos a CloudFront para usar la clave.

En tu configuración original, la clave KMS no tenía una política que permitiera específicamente a CloudFront acceder a los recursos encriptados. La solución consiste en añadir una declaración de política que otorgue los permisos necesarios (`kms:Decrypt`, `kms:Encrypt`, `kms:GenerateDataKey`) al servicio de CloudFront.

## Recomendaciones de seguridad

Aunque hemos implementado una solución que funciona, hay algunas mejoras de seguridad que podrías considerar para el futuro:

1. **Mejora la seguridad de CSP**: Aunque `'unsafe-inline'` resuelve el problema, es mejor a largo plazo:
   - Mover todos los estilos a archivos CSS externos
   - Mover código JavaScript a archivos externos
   - O utilizar hashes o nonces para scripts y estilos que deben ser inline

2. **Gestión de claves KMS**: Documenta y revisa periódicamente tus políticas de KMS para evitar problemas de acceso. Es una buena práctica seguir el principio de menor privilegio.

3. **Pruebas integrales**: Antes de futuros despliegues, realiza pruebas completas que incluyan la verificación de políticas de seguridad y acceso entre servicios.
