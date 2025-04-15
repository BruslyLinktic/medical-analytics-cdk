import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

from medical_analytics.storage_stack import StorageStack

def test_s3_bucket_created():
    """Verifica que se cree el bucket S3 con la configuración correcta."""
    # Crear stack para pruebas
    app = cdk.App()
    stack = StorageStack(app, "TestStorage")
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(stack)
    
    # Verificar que el bucket existe con las propiedades correctas
    template.has_resource("AWS::S3::Bucket", {
        "Properties": {
            "BucketName": "medical-analytics-project-dev",
            "VersioningConfiguration": {
                "Status": "Enabled"
            },
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": Match.array_with([
                    Match.object_like({
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms"
                        }
                    })
                ])
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        }
    })

def test_kms_key_created():
    """Verifica que se cree la clave KMS para encriptación."""
    # Crear stack para pruebas
    app = cdk.App()
    stack = StorageStack(app, "TestStorage")
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(stack)
    
    # Verificar que la clave KMS existe con la configuración correcta
    template.has_resource("AWS::KMS::Key", {
        "Properties": {
            "EnableKeyRotation": True,
            "PendingWindowInDays": 7,
            "Description": "Clave KMS para encriptar datos médicos sensibles"
        }
    })

def test_iam_roles_created():
    """Verifica que se creen los roles IAM con los permisos adecuados."""
    # Crear stack para pruebas
    app = cdk.App()
    stack = StorageStack(app, "TestStorage")
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(stack)
    
    # Verificar que existen los roles IAM esperados
    template.resource_count_is("AWS::IAM::Role", 3)  # Ingestion, ETL, Visualization
    
    # Verificar rol de ingesta
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    }
                }
            ]
        }
    })
    
    # Verificar rol ETL
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "glue.amazonaws.com"
                    }
                }
            ]
        }
    })
    
    # Verificar rol de análisis
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["athena.amazonaws.com", "quicksight.amazonaws.com"]
                    }
                }
            ],
            "Version": "2012-10-17"
        }
    })

def test_lifecycle_configuration():
    """Verifica que el bucket tenga configuradas reglas de ciclo de vida."""
    # Crear stack para pruebas
    app = cdk.App()
    stack = StorageStack(app, "TestStorage")
    
    # Sintetizar CloudFormation template
    template = Template.from_stack(stack)
    
    # Verificar que existe la configuración de ciclo de vida
    template.has_resource_properties("AWS::S3::Bucket", {
        "LifecycleConfiguration": {
            "Rules": Match.array_with([
                Match.object_like({
                    "Status": "Enabled",
                    "NoncurrentVersionTransitions": Match.array_with([
                        Match.object_like({
                            "StorageClass": "STANDARD_IA",
                            "TransitionInDays": 30
                        }),
                        Match.object_like({
                            "StorageClass": "GLACIER",
                            "TransitionInDays": 90
                        })
                    ])
                })
            ])
        }
    })
