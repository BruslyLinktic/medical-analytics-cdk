from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_kms as kms,
    aws_sns as sns
)
from constructs import Construct

class StorageStack(Stack):
    """
    Stack para la capa de almacenamiento del sistema de analítica médica.
    Implementa el bucket S3 con su estructura de carpetas, políticas de seguridad,
    y roles IAM necesarios para operar el sistema.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Crear clave KMS para encriptar los datos médicos
        # Crear clave KMS para encriptar los datos médicos con permisos adicionales para CloudFront
        encryption_key = kms.Key(
            self, 
            "MedicalAnalyticsEncryptionKey",
            alias="medical-analytics-key",
            enable_key_rotation=True,
            pending_window=Duration.days(7),
            description="Clave KMS para encriptar datos médicos sensibles"
        )
        
        # Agregar permisos para que CloudFront pueda usar la clave
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

        # Crear bucket S3 para almacenar los datos médicos
        bucket = s3.Bucket(
            self,
            "MedicalAnalyticsBucket",
            bucket_name="medical-analytics-project-dev",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN
        )

        # Configurar política de ciclo de vida para mover versiones antiguas a almacenamiento más económico
        bucket.add_lifecycle_rule(
            id="archive-old-versions",
            enabled=True,
            noncurrent_versions_to_retain=5,
            noncurrent_version_transitions=[
                s3.NoncurrentVersionTransition(
                    storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                    transition_after=Duration.days(30)
                ),
                s3.NoncurrentVersionTransition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=Duration.days(90)
                )
            ]
        )

        # Crear estructura de carpetas en el bucket S3
        self._create_folder_structure(bucket)

        # Crear roles IAM básicos
        self._create_iam_roles(bucket, encryption_key)

        # Exportar el ARN del bucket como salida del stack
        self.bucket = bucket
        self.bucket_arn = bucket.bucket_arn
        self.encryption_key = encryption_key
        self.encryption_key_arn = encryption_key.key_arn

    def create_error_topic(self, id_base: str) -> sns.Topic:
        """
        Crea un tópico SNS para notificaciones de error en este stack.
        Esto evita dependencias cíclicas entre stacks.
        """
        error_topic = sns.Topic(
            self, 
            id_base,
            display_name="Errores de Ingesta de Datos Médicos",
            topic_name="medical-analytics-errors"
        )
        
        return error_topic

    def _create_folder_structure(self, bucket: s3.Bucket) -> None:
        """
        Nota: En S3 no hay necesidad de crear carpetas explícitamente.
        Las "carpetas" son conceptos lógicos basados en prefijos de nombres de objetos.
        Los objetos se crearán con las rutas correctas durante el funcionamiento normal del sistema.
        
        La estructura esperada será:
        - raw/api/
        - raw/excel/
        - cleaned/pacientes/
        - cleaned/diagnosticos/
        - curated/indicadores/hta/
        - curated/indicadores/dm/
        - curated/agregados/
        """
        # En AWS S3, las carpetas son conceptos lógicos y no necesitan crearse explícitamente
        # Las carpetas aparecerán automáticamente cuando se creen objetos con esos prefijos
        pass

    def _create_iam_roles(self, bucket: s3.Bucket, key: kms.Key) -> None:
        """
        Crea los roles IAM necesarios para operar el sistema.
        """
        # Rol para la ingesta de datos
        ingestion_role = iam.Role(
            self, 
            "MedicalAnalyticsIngestionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Rol para funciones Lambda de ingesta de datos médicos"
        )
        
        # Permisos para acceso al bucket S3 (solo carpeta raw)
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    bucket.arn_for_objects("raw/*"),
                    bucket.bucket_arn
                ]
            )
        )
        
        # Permisos para usar la clave KMS
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                resources=[key.key_arn]
            )
        )
        
        # Permisos básicos para CloudWatch Logs
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["arn:aws:logs:*:*:*"]
            )
        )

        # Permisos para SNS (publicación de mensajes de error)
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                resources=["*"]  # Se limitará a nivel de tópico SNS
            )
        )

        # Rol para procesamiento ETL
        etl_role = iam.Role(
            self, 
            "MedicalAnalyticsETLRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            description="Rol para trabajos de AWS Glue de procesamiento ETL"
        )
        
        # Permisos para acceso al bucket S3 (lectura raw, escritura cleaned y curated)
        etl_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[
                    bucket.arn_for_objects("raw/*"),
                    bucket.bucket_arn
                ]
            )
        )
        
        etl_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
                resources=[
                    bucket.arn_for_objects("cleaned/*"),
                    bucket.arn_for_objects("curated/*"),
                    bucket.bucket_arn
                ]
            )
        )
        
        # Permisos para usar la clave KMS
        etl_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                resources=[key.key_arn]
            )
        )
        
        # Rol para análisis y visualización
        analytics_role = iam.Role(
            self, 
            "MedicalAnalyticsVisualizationRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("athena.amazonaws.com"),
                iam.ServicePrincipal("quicksight.amazonaws.com")
            ),
            description="Rol para servicios de análisis y visualización"
        )
        
        # Permisos para acceso de lectura a datos procesados
        analytics_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[
                    bucket.arn_for_objects("cleaned/*"),
                    bucket.arn_for_objects("curated/*"),
                    bucket.bucket_arn
                ]
            )
        )
        
        # Permisos para usar la clave KMS (solo desencriptar)
        analytics_role.add_to_policy(
            iam.PolicyStatement(
                actions=["kms:Decrypt"],
                resources=[key.key_arn]
            )
        )
        
        # Almacenamos los roles como propiedades del stack para referencia futura
        self.ingestion_role = ingestion_role
        self.etl_role = etl_role
        self.analytics_role = analytics_role
