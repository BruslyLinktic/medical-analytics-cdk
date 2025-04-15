import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

from medical_analytics.storage_stack import StorageStack
from medical_analytics.ingestion_stack import IngestionStack

def test_api_ingestion_lambda_created():
    """Verifica que se cree la función Lambda para ingesta desde API."""
    # Crear stacks para pruebas
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorage")
    ingestion_stack = IngestionStack(
        app, 
        "TestIngestion",
        storage_bucket=storage_stack.bucket,
        storage_key_arn=storage_stack.encryption_key_arn,
        ingestion_role=storage_stack.ingestion_role
    )
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(ingestion_stack)
    
    # Verificar que la función Lambda existe con las propiedades correctas
    template.has_resource("AWS::Lambda::Function", {
        "Properties": {
            "FunctionName": "medical-analytics-api-ingestion",
            "Runtime": "python3.9",
            "Timeout": 300,  # 5 minutos
            "MemorySize": 256,
            "Handler": "index.handler"
        }
    })

def test_file_processor_lambda_created():
    """Verifica que se cree la función Lambda para procesar archivos."""
    # Crear stacks para pruebas
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorage")
    ingestion_stack = IngestionStack(
        app, 
        "TestIngestion",
        storage_bucket=storage_stack.bucket,
        storage_key_arn=storage_stack.encryption_key_arn,
        ingestion_role=storage_stack.ingestion_role
    )
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(ingestion_stack)
    
    # Verificar que la función Lambda existe con las propiedades correctas
    template.has_resource("AWS::Lambda::Function", {
        "Properties": {
            "FunctionName": "medical-analytics-file-processor",
            "Runtime": "python3.9",
            "Timeout": 30,
            "MemorySize": 512,
            "Handler": "index.handler"
        }
    })

def test_api_gateway_created():
    """Verifica que se cree la API Gateway para carga de archivos."""
    # Crear stacks para pruebas
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorage")
    ingestion_stack = IngestionStack(
        app, 
        "TestIngestion",
        storage_bucket=storage_stack.bucket,
        storage_key_arn=storage_stack.encryption_key_arn,
        ingestion_role=storage_stack.ingestion_role
    )
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(ingestion_stack)
    
    # Verificar que la API Gateway existe
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    
    # Verificar configuración de CORS
    template.has_resource_properties("AWS::ApiGateway::RestApi", {
        "Name": "Sistema de Analítica Médica"
    })

def test_event_rules_created():
    """Verifica que se creen las reglas de EventBridge para las ejecuciones programadas."""
    # Crear stacks para pruebas
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorage")
    ingestion_stack = IngestionStack(
        app, 
        "TestIngestion",
        storage_bucket=storage_stack.bucket,
        storage_key_arn=storage_stack.encryption_key_arn,
        ingestion_role=storage_stack.ingestion_role
    )
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(ingestion_stack)
    
    # Verificar que existen 4 reglas de EventBridge
    template.resource_count_is("AWS::Events::Rule", 4)

def test_frontend_bucket_created():
    """Verifica que se cree el bucket S3 para el frontend."""
    # Crear stacks para pruebas
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorage")
    ingestion_stack = IngestionStack(
        app, 
        "TestIngestion",
        storage_bucket=storage_stack.bucket,
        storage_key_arn=storage_stack.encryption_key_arn,
        ingestion_role=storage_stack.ingestion_role
    )
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(ingestion_stack)
    
    # Verificar que el bucket existe con la configuración correcta
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketName": "medical-analytics-frontend-dev",
        "WebsiteConfiguration": {
            "IndexDocument": "index.html",
            "ErrorDocument": "index.html"
        }
    })

def test_sns_topic_created():
    """Verifica que se cree el tópico SNS para notificaciones de error."""
    # Crear stacks para pruebas
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorage")
    ingestion_stack = IngestionStack(
        app, 
        "TestIngestion",
        storage_bucket=storage_stack.bucket,
        storage_key_arn=storage_stack.encryption_key_arn,
        ingestion_role=storage_stack.ingestion_role
    )
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(ingestion_stack)
    
    # Verificar que el tópico SNS existe
    template.has_resource_properties("AWS::SNS::Topic", {
        "DisplayName": "Errores de Ingesta de Datos Médicos",
        "TopicName": "medical-analytics-errors"
    })
