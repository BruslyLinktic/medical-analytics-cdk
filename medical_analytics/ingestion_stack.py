from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_sns as sns,
    CfnOutput
)
from constructs import Construct

class IngestionStack(Stack):
    """
    Stack para la capa de ingesta de datos del sistema de analítica médica.
    Implementa dos rutas de ingesta:
    1. Componente para consumir la API del cliente periódicamente
    2. API Gateway para recibir archivos Excel cargados por usuarios
    """

    def __init__(self, scope: Construct, construct_id: str, 
                 storage_bucket: s3.IBucket, 
                 storage_key_arn: str, 
                 ingestion_role: iam.IRole,
                 error_topic: sns.ITopic,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Referencias a recursos del stack de almacenamiento
        self.bucket = storage_bucket
        self.key_arn = storage_key_arn
        self.ingestion_role = ingestion_role
        self.error_topic = error_topic
        
        # Implementar componentes de ingesta
        self.api_ingestion_lambda = self._create_api_ingestion_component()
        self.upload_api, self.file_processor_lambda = self._create_file_upload_api()
        self.frontend_url = self._create_frontend()
        
        # Crear salidas del stack
        CfnOutput(
            self,
            "ApiEndpoint",
            description="Endpoint de la API para carga de archivos",
            value=f"{self.upload_api.url}upload"
        )
        
        CfnOutput(
            self,
            "FrontendUrl",
            description="URL del frontend para carga de archivos",
            value=self.frontend_url
        )
        
        CfnOutput(
            self,
            "ErrorTopicArn",
            description="ARN del tópico SNS para notificaciones de error",
            value=self.error_topic.topic_arn
        )
        
    def _create_api_ingestion_component(self):
        """
        Crea una función Lambda para consumir la API del cliente y
        almacenar los datos en S3, programada para ejecutarse 4 veces al día.
        """
        # Crear función Lambda para ingesta de API
        api_ingestion_lambda = lambda_.Function(
            self,
            "ApiIngestionLambda",
            function_name="medical-analytics-api-ingestion",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda/api_ingestion"),
            handler="index.handler",
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "API_ENDPOINT": "https://api.ejemplo.com/datos-medicos",  # Reemplazar con la API real
                "API_KEY": "{{API_KEY_PLACEHOLDER}}"  # Reemplazar en producción
            },
            role=self.ingestion_role,
            description="Función para ingestar datos desde la API del cliente"
        )
        
        # Configurar registro de logs detallado
        api_ingestion_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:PutLogEvents", "logs:CreateLogStream", "logs:CreateLogGroup"],
                resources=["arn:aws:logs:*:*:*"]
            )
        )
        
        # Crear reglas de EventBridge para ejecuciones programadas
        schedule_expressions = [
            "cron(0 9 * * ? *)",    # 9:00 AM UTC
            "cron(0 13 * * ? *)",   # 1:00 PM UTC
            "cron(0 17 * * ? *)",   # 5:00 PM UTC
            "cron(0 21 * * ? *)"    # 9:00 PM UTC
        ]
        
        for idx, expression in enumerate(schedule_expressions):
            events.Rule(
                self,
                f"ApiIngestionSchedule{idx + 1}",
                schedule=events.Schedule.expression(expression),
                targets=[targets.LambdaFunction(api_ingestion_lambda)],
                description=f"Programación {idx + 1} para ingesta de datos médicos desde API"
            )
        
        return api_ingestion_lambda
        
    def _create_file_upload_api(self):
        """
        Crea una API con API Gateway para recibir archivos Excel
        y una función Lambda para procesarlos y guardarlos en S3.
        """
        # Crear función Lambda para procesar archivos
        file_processor_lambda = lambda_.Function(
            self,
            "FileProcessorLambda",
            function_name="medical-analytics-file-processor",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda/file_processor"),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "ERROR_TOPIC_ARN": self.error_topic.topic_arn
            },
            role=self.ingestion_role,
            description="Función para procesar archivos Excel médicos"
        )
        
        # Otorgar permisos para publicar en SNS
        file_processor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                resources=[self.error_topic.topic_arn]
            )
        )
        
        # Configurar API Gateway
        api = apigateway.RestApi(
            self,
            "MedicalAnalyticsUploadApi",
            rest_api_name="Sistema de Analítica Médica",
            description="API para carga de archivos Excel con datos médicos",
            binary_media_types=["*/*"],  # Permitir contenido binario
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # Crear recurso y método de API
        upload_resource = api.root.add_resource("upload")
        upload_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                file_processor_lambda,
                proxy=True,
                content_handling=apigateway.ContentHandling.CONVERT_TO_TEXT
            ),
            api_key_required=True  # Requerir API key para seguridad
        )
        
        # Crear plan de uso y API key
        plan = api.add_usage_plan(
            "MedicalAnalyticsUsagePlan",
            name="medical-analytics-usage-plan",
            description="Plan de uso para API de carga de archivos médicos",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            ),
            quota=apigateway.QuotaSettings(
                limit=100,  # 100 solicitudes
                period=apigateway.Period.DAY
            )
        )
        
        api_key = api.add_api_key("MedicalAnalyticsApiKey", api_key_name="medical-analytics-api-key")
        plan.add_api_key(api_key)
        plan.add_api_stage(stage=api.deployment_stage)
        
        return api, file_processor_lambda
        
    def _create_frontend(self):
        """
        Crea un frontend simple para la carga de archivos usando CloudFront
        para acceso seguro en lugar de habilitar acceso público directo al bucket S3.
        """
        # Crear bucket para alojar el frontend (SIN acceso público)
        frontend_bucket = s3.Bucket(
            self,
            "MedicalAnalyticsFrontendBucket",
            bucket_name="medical-analytics-frontend-dev",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Bloqueamos todo acceso público
            removal_policy=RemovalPolicy.DESTROY  # Eliminar el bucket cuando se destruya el stack
        )
        
        # Crear una distribución CloudFront para servir el contenido del frontend de forma segura
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, 
            "MedicalAnalyticsFrontendOAI",
            comment="OAI para acceder al bucket de frontend de Medical Analytics"
        )
        
        # Otorgar permisos de lectura a CloudFront OAI
        frontend_bucket.grant_read(origin_access_identity)
        
        # Crear distribución CloudFront
        distribution = cloudfront.Distribution(
            self,
            "MedicalAnalyticsFrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    bucket=frontend_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"  # SPA handling
                )
            ]
        )
        
        # Se podría agregar un despliegue inicial de archivos (opcional)
        # s3_deployment.BucketDeployment(
        #     self,
        #     "MedicalAnalyticsFrontendDeployment",
        #     sources=[s3_deployment.Source.asset("frontend/build")],
        #     destination_bucket=frontend_bucket,
        #     distribution=distribution,
        #     distribution_paths=["/*"]
        # )
        
        # Obtener URL del frontend (usando CloudFront)
        frontend_url = f"https://{distribution.distribution_domain_name}"
        
        # Almacenar referencias para uso futuro
        self.frontend_bucket = frontend_bucket
        self.frontend_distribution = distribution
        
        return frontend_url
