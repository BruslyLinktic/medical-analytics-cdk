from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_sns as sns,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    CfnOutput
)
from constructs import Construct
import os
import tempfile

class IngestionStack(Stack):
    """
    Stack para la capa de ingesta de datos del sistema de analítica médica.
    Implementa componentes para ingestar datos médicos desde la API del cliente
    y a través de una interfaz web para carga de archivos Excel.
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        storage_bucket: s3.Bucket,
        storage_key_arn: str,
        ingestion_role: iam.Role,
        error_topic: sns.Topic,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Referencia a recursos externos
        self.bucket = storage_bucket
        self.encryption_key_arn = storage_key_arn
        self.error_topic = error_topic
        self.ingestion_role = ingestion_role

        # 1. Implementación de Componente de Ingesta API
        api_lambda = self._create_api_ingestion_lambda(storage_bucket.bucket_name)
        
        # 2. EventBridge para ejecución programada de la ingesta API
        self._create_api_ingestion_schedule(api_lambda)
        
        # 3. API Gateway para Carga de Archivos
        api_gateway, api_key_value = self._create_upload_api()
        
        # 4. Función Lambda para Procesamiento de Archivos
        file_processor_lambda = self._create_file_processor_lambda(
            storage_bucket.bucket_name, 
            error_topic.topic_arn
        )
        
        # 5. Integración de API Gateway con Lambda
        self._integrate_api_with_lambda(api_gateway, file_processor_lambda)
        
        # Guardar referencias para uso externo
        self.api_gateway_url = api_gateway.url
        self.api_key_value = api_key_value
        
        # Outputs
        CfnOutput(self, "ApiEndpoint", value=f"{api_gateway.url}")
        CfnOutput(self, "ApiKeyOutput", value=api_key_value, description="API Key para usar en el frontend")

    def _create_api_ingestion_lambda(self, bucket_name: str) -> lambda_.Function:
        """
        Crea la función Lambda para ingesta desde la API.
        """
        lambda_fn = lambda_.Function(
            self, 
            "ApiIngestionFunction",
            function_name="medical-analytics-api-ingestion",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda/api_ingestion"),
            handler="index.handler",
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "BUCKET_NAME": bucket_name,
                "API_ENDPOINT": "https://api.ejemplo.com/datos-medicos",  # Reemplazar con URL real
                "API_KEY": "placeholder-api-key"  # En producción usar secretos
            },
            role=self.ingestion_role
        )
        
        return lambda_fn

    def _create_api_ingestion_schedule(self, lambda_fn: lambda_.Function) -> None:
        """
        Configura la ejecución programada de la función de ingesta API.
        """
        # Regla para 9:00 AM UTC
        events.Rule(
            self, 
            "IngestionSchedule9AM",
            schedule=events.Schedule.cron(
                minute="0",
                hour="9",
                day="*",
                month="*",
                year="*"
            ),
            targets=[targets.LambdaFunction(lambda_fn)]
        )
        
        # Regla para 1:00 PM UTC
        events.Rule(
            self, 
            "IngestionSchedule1PM",
            schedule=events.Schedule.cron(
                minute="0",
                hour="13",
                day="*",
                month="*",
                year="*"
            ),
            targets=[targets.LambdaFunction(lambda_fn)]
        )
        
        # Regla para 5:00 PM UTC
        events.Rule(
            self, 
            "IngestionSchedule5PM",
            schedule=events.Schedule.cron(
                minute="0",
                hour="17",
                day="*",
                month="*",
                year="*"
            ),
            targets=[targets.LambdaFunction(lambda_fn)]
        )
        
        # Regla para 9:00 PM UTC
        events.Rule(
            self, 
            "IngestionSchedule9PM",
            schedule=events.Schedule.cron(
                minute="0",
                hour="21",
                day="*",
                month="*",
                year="*"
            ),
            targets=[targets.LambdaFunction(lambda_fn)]
        )

    def _create_upload_api(self) -> tuple[apigw.RestApi, apigw.ApiKey]:
        """
        Crea la API Gateway para la carga de archivos.
        """
        # Crear la API REST
        api = apigw.RestApi(
            self, 
            "MedicalAnalyticsUploadApi",
            rest_api_name="medical-analytics-upload-api",
            description="API para carga de archivos Excel con datos médicos",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],  # En producción, limitar a dominios específicos
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "Origin", "Accept"],
                allow_credentials=True,
                max_age=Duration.seconds(300)  # Tiempo de caché para respuestas preflight
            ),
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=10,
                throttling_burst_limit=20,
            ),
            binary_media_types=["multipart/form-data", "application/octet-stream"]  # Soporte para tipos binarios
        )
        
        # Crear plan de uso y API key
        plan = api.add_usage_plan(
            "MedicalAnalyticsUsagePlan",
            name="medical-analytics-usage-plan",
            throttle=apigw.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            ),
            quota=apigw.QuotaSettings(
                limit=100,
                period=apigw.Period.DAY
            )
        )
        
        # Crear una API key con un valor que podamos conocer para desarrollo
        # En producción, se debería usar otro método más seguro
        api_key_value = "test-medical-analytics-key-123"
        api_key = api.add_api_key(
            "MedicalAnalyticsApiKey", 
            api_key_name="medical-analytics-api-key",
            value=api_key_value
        )
        plan.add_api_key(api_key)
        
        # Crear una salida para obtener la API key
        CfnOutput(self, "ApiKeyValue", value=api_key_value, description="API Key para usar en el frontend")
        
        return api, api_key_value

    def _create_file_processor_lambda(self, bucket_name: str, topic_arn: str) -> lambda_.Function:
        """
        Crea la función Lambda para procesamiento de archivos.
        """
        lambda_fn = lambda_.Function(
            self, 
            "FileProcessorFunction",
            function_name="medical-analytics-file-processor",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda/file_processor"),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "BUCKET_NAME": bucket_name,
                "ERROR_TOPIC_ARN": topic_arn
            },
            role=self.ingestion_role
        )
        
        return lambda_fn

    def _integrate_api_with_lambda(self, api: apigw.RestApi, lambda_fn: lambda_.Function) -> None:
        """
        Integra la API Gateway con la función Lambda de procesamiento de archivos.
        """
        # Crear recurso /upload
        upload_resource = api.root.add_resource("upload")
        
        # Integración con Lambda
        upload_integration = apigw.LambdaIntegration(
            lambda_fn,
            proxy=True,
            content_handling=apigw.ContentHandling.CONVERT_TO_TEXT,
            integration_responses=[
                {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Origin": "'*'",  # En producción, limitar a dominio CloudFront
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,Origin,Accept'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Credentials": "'true'"
                    }
                },
                {
                    "statusCode": "400",
                    "selectionPattern": ".*[Bad Request].*",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,Origin,Accept'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Credentials": "'true'"
                    }
                },
                {
                    "statusCode": "500",
                    "selectionPattern": ".*[Error].*",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,Origin,Accept'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Credentials": "'true'"
                    }
                }
            ]
        )
        
        # Agregar método POST con integración
        upload_resource.add_method(
            "POST",
            upload_integration,
            api_key_required=True,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    },
                    response_models={
                        "application/json": apigw.Model.EMPTY_MODEL
                    }
                ),
                apigw.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    },
                    response_models={
                        "application/json": apigw.Model.ERROR_MODEL
                    }
                ),
                apigw.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    },
                    response_models={
                        "application/json": apigw.Model.ERROR_MODEL
                    }
                )
            ]
        )
        
        # No necesitamos agregar explícitamente el método OPTIONS para CORS
        # porque API Gateway lo crea automáticamente cuando usamos default_cors_preflight_options
        # en la definición del RestApi


