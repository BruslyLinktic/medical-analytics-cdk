# Cambios Realizados en el Proyecto Medical Analytics CDK

Este documento detalla las correcciones realizadas en el código del proyecto para solucionar los diversos problemas que se estaban enfrentando durante el despliegue y ejecución de la aplicación.

## Resumen de Problemas Solucionados

1. **Configuración CSP en CloudFront**: Se agregó 'unsafe-inline' para permitir estilos y scripts inline.
2. **Políticas KMS**: Se agregaron permisos explícitos para que CloudFront pueda acceder a los recursos encriptados.
3. **Problemas CORS**: Se corrigió la configuración CORS de API Gateway y se modificó el frontend para evitar conflictos.

## Cambios Detallados

### 1. Corrección de Content Security Policy (CSP) en CloudFront

**Archivo**: `/medical_analytics/cdn_stack/cdn_stack.py`

Se modificó la política CSP para permitir scripts y estilos inline, lo que es necesario para el funcionamiento adecuado del frontend:

```python
content_security_policy=cloudfront.ResponseHeadersContentSecurityPolicy(
    content_security_policy="default-src 'self'; img-src 'self' https://cdn-icons-png.flaticon.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;",
    override=True
)
```

### 2. Permisos para CloudFront en la Clave KMS

**Archivo**: `/medical_analytics/storage_stack.py`

Se agregó una política explícita a la clave KMS para permitir que CloudFront pueda acceder a los recursos encriptados:

```python
encryption_key.add_to_resource_policy(
    iam.PolicyStatement(
        sid="AllowCloudFrontServiceAccess",
        effect=iam.Effect.ALLOW,
        principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
        actions=[
            "kms:Decrypt",
            "kms:Encrypt",
            "kms:GenerateDataKey"
        ],
        resources=["*"]
    )
)
```

### 3. Modificaciones para Resolver Problemas CORS

#### 3.1 Cambio en Frontend HTML

**Archivo**: `/frontend/index.html`

Se modificó la configuración fetch para usar `credentials: 'same-origin'` en lugar de `credentials: 'include'`, lo que evita problemas de CORS cuando se usan comodines (*) en las políticas de origen permitido:

```javascript
fetch(API_URL, {
    method: 'POST',
    mode: 'cors',
    credentials: 'same-origin', // Cambiado de 'include' para evitar problemas CORS
    headers: {
        'Content-Type': 'application/json',
        'x-api-key': '{{API_KEY}}'
    },
    body: JSON.stringify(data)
})
```

#### 3.2 Cambios en la Configuración CORS de API Gateway

**Archivo**: `/medical_analytics/ingestion_stack.py`

Se modificó la configuración CORS del API Gateway para no incluir `allow_credentials=True` cuando se usa `allow_origins=["*"]`, ya que esto viola las reglas de seguridad CORS:

```python
default_cors_preflight_options=apigw.CorsOptions(
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "Origin", "Accept"],
    allow_credentials=False,  # Cambiado a False para ser compatible con allow_origins=["*"]
    max_age=Duration.seconds(300)
)
```

También se eliminaron todas las referencias a la cabecera `Access-Control-Allow-Credentials` en las respuestas de integración y en los method_responses.

## Explicación Técnica de los Problemas

### Problema CSP (Content Security Policy)

El CSP es un mecanismo de seguridad que ayuda a prevenir ataques de inyección de código como XSS. En la configuración original, no se permitían scripts ni estilos inline, lo que estaba bloqueando el funcionamiento correcto del frontend que utiliza estos elementos.

### Problema KMS

AWS Key Management Service (KMS) utiliza políticas de acceso para controlar quién puede utilizar las claves de encriptación. Sin permisos explícitos, CloudFront no podía acceder a los recursos encriptados.

### Problema CORS

Cross-Origin Resource Sharing (CORS) es un mecanismo de seguridad que controla las solicitudes HTTP entre diferentes orígenes. Había dos problemas principales:

1. **Uso de `credentials: 'include'` con `Access-Control-Allow-Origin: '*'`**: Las especificaciones de CORS prohíben esta combinación por motivos de seguridad. No se puede usar el comodín '*' cuando se envían credenciales.

2. **Cabeceras inconsistentes**: La configuración inconsistente entre el cliente y el servidor estaba causando errores de CORS.

## Recomendaciones Adicionales

Para entornos de producción, se recomienda:

1. **Especificar los orígenes permitidos**: En lugar de usar el comodín '*', listar explícitamente los dominios permitidos:
   ```python
   allow_origins=["https://d2fypua5bbhj7a.cloudfront.net"]
   ```

2. **Externalizar estilos y scripts**: Mover los estilos y scripts inline a archivos externos, lo que permitiría usar una CSP más restrictiva.

3. **Añadir monitoreo de CORS**: Implementar un sistema de monitoreo para detectar errores de CORS rápidamente.
