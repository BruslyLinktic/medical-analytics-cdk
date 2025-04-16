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
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct
import os
import tempfile
import uuid
import json

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
        
        # 3. API Gateway para Carga de Archivos con secreto para la API key
        api_gateway, api_key_secret = self._create_upload_api()
        
        # 4. Función Lambda para Procesamiento de Archivos
        file_processor_lambda = self._create_file_processor_lambda(
            storage_bucket.bucket_name, 
            error_topic.topic_arn
        )
        
        # 5. Integración de API Gateway con Lambda
        self._integrate_api_with_lambda(api_gateway, file_processor_lambda)
        
        # 6. Implementar monitoreo y alarmas para las funciones Lambda
        self._setup_monitoring(api_lambda, file_processor_lambda)
        
        # Guardar referencias para uso externo
        self.api_gateway_url = api_gateway.url
        self.api_key_secret = api_key_secret
        
        # Outputs
        CfnOutput(self, "ApiEndpoint", value=f"{api_gateway.url}")
        CfnOutput(self, "ApiKeySecretArn", value=api_key_secret.secret_arn)
        # Agregamos una función para recuperar el valor de la API key (solo para desarrollo)
        CfnOutput(self, "GetApiKeyCommand", value=f"aws secretsmanager get-secret-value --secret-id {api_key_secret.secret_name} --query 'SecretString' --output text")

    def _create_api_ingestion_lambda(self, bucket_name: str) -> lambda_.Function:
        """
        Crea la función Lambda para ingesta desde la API.
        """
        # Crear grupo de logs con retención configurada
        log_group = logs.LogGroup(
            self,
            "ApiIngestionLogGroup",
            log_group_name="/aws/lambda/medical-analytics-api-ingestion",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Secret para la API key externa (en lugar de hard-coding)
        external_api_key = secretsmanager.Secret(
            self,
            "ExternalApiKeySecret",
            description="API Key para acceder a la API externa de datos médicos",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                password_length=32
            )
        )
        
        # Lambda function con tracing activado y configuración mejorada
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
                "SECRET_NAME": external_api_key.secret_name,  # Referencia al secreto, no la API key directamente
                "ERROR_TOPIC_ARN": self.error_topic.topic_arn
            },
            role=self.ingestion_role,
            tracing=lambda_.Tracing.ACTIVE,  # Habilitar AWS X-Ray
            log_retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Dar permiso a la Lambda para leer el secreto
        external_api_key.grant_read(lambda_fn)
        
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

    def _create_upload_api(self) -> tuple[apigw.RestApi, secretsmanager.Secret]:
        """
        Crea la API Gateway para la carga de archivos usando Secrets Manager para la API key.
        """
        # Crear la API REST con mejor configuración de seguridad
        api = apigw.RestApi(
            self, 
            "MedicalAnalyticsUploadApi",
            rest_api_name="medical-analytics-upload-api",
            description="API para carga de archivos Excel con datos médicos",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],  # En producción, limitar a dominio de CloudFront
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "Origin", "Accept"],
                allow_credentials=True,
                max_age=Duration.seconds(300)
            ),
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=10,
                throttling_burst_limit=20,
                logging_level=apigw.MethodLoggingLevel.INFO,  # Activar logs para debug
                metrics_enabled=True,  # Activar métricas de API Gateway
                data_trace_enabled=True,  # Solo para desarrollo, deshabilitar en producción
            ),
            binary_media_types=["multipart/form-data", "application/octet-stream"],
            minimum_compression_size=1024,  # Comprimir respuestas de más de 1KB
        )
        
        # Crear plan de uso
        plan = api.add_usage_plan(
            "MedicalAnalyticsUsagePlan",
            name="medical-analytics-usage-plan",
            throttle=apigw.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            ),
            quota=apigw.QuotaSettings(
                limit=1000,  # Aumentado a un valor más razonable
                period=apigw.Period.MONTH
            )
        )
        
        # Crear un secreto en Secrets Manager para la API key
        api_key_secret = secretsmanager.Secret(
            self,
            "ApiKeySecret",
            description="API Key para acceso a la API de carga de archivos médicos",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                password_length=32
            )
        )
        
        # Recuperar el valor generado para la API key (esto crea una dependencia circular,
        # pero es necesario para configurar correctamente la API key en API Gateway)
        api_key_value = api_key_secret.secret_value.to_string()
        
        # Crear la API key con el valor del secreto
        api_key = api.add_api_key(
            "MedicalAnalyticsApiKey", 
            api_key_name="medical-analytics-api-key",
            value=api_key_value
        )
        
        # Agregar la API key al plan de uso
        plan.add_api_key(api_key)
        
        return api, api_key_secret

    def _create_file_processor_lambda(self, bucket_name: str, topic_arn: str) -> lambda_.Function:
        """
        Crea la función Lambda para procesamiento de archivos.
        """
        # Crear grupo de logs con retención configurada
        log_group = logs.LogGroup(
            self,
            "FileProcessorLogGroup",
            log_group_name="/aws/lambda/medical-analytics-file-processor",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Lambda function con tracing activado y configuración mejorada
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
            role=self.ingestion_role,
            tracing=lambda_.Tracing.ACTIVE,  # Habilitar AWS X-Ray
            log_retention=logs.RetentionDays.ONE_MONTH
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
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
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

    def _setup_monitoring(self, api_lambda: lambda_.Function, file_processor_lambda: lambda_.Function) -> None:
        """
        Configura monitoreo y alarmas para las funciones Lambda.
        """
        # Alarma para errores en la función de ingesta API
        api_errors_alarm = cloudwatch.Alarm(
            self,
            "ApiIngestionErrorsAlarm",
            metric=api_lambda.metric_errors(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alarma por errores en la ingesta desde API",
            alarm_name="MedicalAnalytics-ApiIngestion-Errors"
        )
        
        # Asociar acción de alarma (notificación SNS)
        api_errors_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.error_topic)
        )
        
        # Alarma para errores en la función de procesamiento de archivos
        file_errors_alarm = cloudwatch.Alarm(
            self,
            "FileProcessorErrorsAlarm",
            metric=file_processor_lambda.metric_errors(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alarma por errores en el procesamiento de archivos",
            alarm_name="MedicalAnalytics-FileProcessor-Errors"
        )
        
        # Asociar acción de alarma (notificación SNS)
        file_errors_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.error_topic)
        )
        
        # Alarma por tiempos de ejecución largos (posibles problemas de rendimiento)
        file_duration_alarm = cloudwatch.Alarm(
            self,
            "FileProcessorDurationAlarm",
            metric=file_processor_lambda.metric_duration(),
            threshold=25000,  # 25 segundos (de 30 máximos)
            evaluation_periods=3,
            datapoints_to_alarm=2,  # Requiere que 2 de 3 evaluaciones superen el umbral
            alarm_description="Alarma por tiempos de procesamiento cercanos al timeout",
            alarm_name="MedicalAnalytics-FileProcessor-LongDuration"
        )
        
        # Asociar acción de alarma (notificación SNS)
        file_duration_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.error_topic)
        )
