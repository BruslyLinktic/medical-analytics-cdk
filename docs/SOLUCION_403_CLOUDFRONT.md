# Solución al Error 403 Forbidden en CloudFront

## Descripción del Problema

El error 403 Forbidden que aparece al acceder a CloudFront se debe a un problema de permisos entre CloudFront y el bucket S3 que aloja el frontend. El mensaje de error "AccessDenied" indica que CloudFront no puede acceder correctamente a los objetos almacenados en S3.

## Causas del Problema

1. **Configuración incompleta de permisos**: A pesar de que en el código CDK se configura un Origin Access Identity (OAI) para CloudFront, esto puede no ser suficiente.

2. **Políticas de bucket restrictivas**: Las políticas de bucket pueden no estar permitiendo explícitamente el acceso a CloudFront.

3. **Configuración del OAI**: El OAI puede no estar correctamente asociado a la distribución CloudFront o a la política del bucket.

## Soluciones Implementadas

Hemos implementado dos soluciones complementarias:

### 1. Solución a nivel de código CDK (`apply_cdn_fix.sh`)

Este script reemplaza el archivo `cdn_stack.py` con una versión corregida que:

- Mantiene el permiso usando el ID canónico de usuario del OAI
- Añade un permiso adicional usando el principal de servicio de CloudFront con una condición para limitar el acceso

Para aplicar esta solución:

```bash
# Hacer ejecutable el script
chmod +x apply_cdn_fix.sh

# Ejecutar el script
./apply_cdn_fix.sh
```

Después de ejecutar este script, deberás redesplegar el stack CDN para aplicar los cambios:

```bash
cdk deploy medical-analytics-cdn-dev
```

### 2. Solución a nivel de AWS (`fix_cloudfront.sh`)

Este script actúa directamente sobre los recursos ya desplegados en AWS para:

- Identificar la distribución CloudFront y el bucket S3 relacionados
- Obtener el OAI configurado
- Actualizar la política del bucket S3 para permitir acceso explícito a CloudFront
- Configurar CORS correctamente

Para aplicar esta solución:

```bash
# Hacer ejecutable el script
chmod +x fix_cloudfront.sh

# Ejecutar el script
./fix_cloudfront.sh
```

## ¿Qué solución debo aplicar?

1. **Si estás desplegando por primera vez**: Aplica `apply_cdn_fix.sh` para asegurar que el código esté correcto antes del despliegue.

2. **Si ya has desplegado y tienes el error 403**: Aplica primero `fix_cloudfront.sh` para corregir los recursos existentes. Si el problema persiste, aplica `apply_cdn_fix.sh` y redesplega.

## Verificación

Para verificar que la solución ha funcionado:

1. Espera unos minutos después de aplicar los cambios (CloudFront puede tardar en propagar)
2. Accede a la URL de CloudFront proporcionada en las salidas del despliegue
3. Deberías ver la interfaz web de carga de archivos sin errores 403

## Explicación Técnica

### ¿Por qué se necesitan ambos permisos?

AWS ha introducido dos mecanismos para controlar el acceso de CloudFront a S3:

1. **OAI (Origin Access Identity)**: El método tradicional, donde CloudFront usa una identidad especial para acceder a S3.
2. **OAC (Origin Access Control)**: El método más nuevo y recomendado, que utiliza el principal de servicio de CloudFront.

Nuestra solución implementa ambos métodos para asegurar la máxima compatibilidad:

```python
# Método 1: OAI con CanonicalUserPrincipal
frontend_bucket.add_to_resource_policy(
    iam.PolicyStatement(
        actions=["s3:GetObject"],
        resources=[frontend_bucket.arn_for_objects("*")],
        principals=[iam.CanonicalUserPrincipal(
            oai.cloud_front_origin_access_identity_s3_canonical_user_id
        )]
    )
)

# Método 2: OAC con ServicePrincipal de CloudFront
frontend_bucket.add_to_resource_policy(
    iam.PolicyStatement(
        sid="AllowCloudFrontServicePrincipal",
        actions=["s3:GetObject"],
        resources=[frontend_bucket.arn_for_objects("*")],
        principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
        conditions={
            "StringEquals": {
                "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/*"
            }
        }
    )
)
```

## Recursos Adicionales

- [AWS CloudFront Origin Access Identity](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [AWS CloudFront Origin Access Control](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-origin.html)
- [AWS CDK CloudFront Documentation](https://docs.aws.amazon.com/cdk/api/latest/docs/aws-cloudfront-readme.html)
