from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_s3 as s3,
    CfnOutput
)
import aws_cdk.aws_lambda_python_alpha as lambda_python
from constructs import Construct
import os

class LambdaLayerStack(Stack):
    """
    Stack para implementar Lambda Layers para el sistema de analítica médica.
    Estos layers son necesarios para incluir las dependencias externas como pandas
    que no están disponibles en el runtime por defecto de Lambda.
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Crear Lambda Layers para dependencias externas
        self.pandas_layer = self._create_pandas_layer()
        self.common_layer = self._create_common_layer()
        
        # Outputs
        CfnOutput(self, "PandasLayerArn", value=self.pandas_layer.layer_version_arn)
        CfnOutput(self, "CommonLayerArn", value=self.common_layer.layer_version_arn)

    def _create_pandas_layer(self) -> lambda_.LayerVersion:
        """
        Crea un Lambda Layer para pandas y dependencias relacionadas.
        """
        # Utilizar lambda-python-alpha para crear un layer de Python
        return lambda_python.PythonLayerVersion(
            self,
            "PandasLayer",
            entry="layers/pandas_layer",  # Directorio con requirements.txt
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_8
            ],
            removal_policy=RemovalPolicy.RETAIN,
            description="Layer con pandas y dependencias para procesamiento de datos en Excel"
        )

    def _create_common_layer(self) -> lambda_.LayerVersion:
        """
        Crea un Lambda Layer para dependencias comunes como boto3, requests, etc.
        """
        # Utilizar lambda-python-alpha para crear un layer de Python
        return lambda_python.PythonLayerVersion(
            self,
            "CommonLayer",
            entry="layers/common_layer",  # Directorio con requirements.txt
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_8
            ],
            removal_policy=RemovalPolicy.RETAIN,
            description="Layer con dependencias comunes como boto3, requests, etc."
        )
