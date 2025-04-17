from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_s3 as s3,
    CfnOutput
)
# import aws_cdk.aws_lambda_python_alpha as lambda_python  # No se usa más para evitar dependencia de Docker
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
        # Comprobar si existe el archivo de la capa preempaquetada
        layer_path = "packaged_layers/pandas_layer.zip"
        if not os.path.exists(layer_path):
            # Si no existe, mostrar mensaje de error con instrucciones
            raise Exception(f"La capa '{layer_path}' no existe. Ejecuta primero './packaged_layers/layer-builder.sh' para empaquetar las capas sin Docker.")
        
        # Crear un lambda layer utilizando el archivo preempaquetado (sin Docker)
        return lambda_.LayerVersion(
            self,
            "PandasLayer",
            code=lambda_.Code.from_asset(layer_path),
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
        # Comprobar si existe el archivo de la capa preempaquetada
        layer_path = "packaged_layers/common_layer.zip"
        if not os.path.exists(layer_path):
            # Si no existe, mostrar mensaje de error con instrucciones
            raise Exception(f"La capa '{layer_path}' no existe. Ejecuta primero './packaged_layers/layer-builder.sh' para empaquetar las capas sin Docker.")
        
        # Crear un lambda layer utilizando el archivo preempaquetado (sin Docker)
        return lambda_.LayerVersion(
            self,
            "CommonLayer",
            code=lambda_.Code.from_asset(layer_path),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_8
            ],
            removal_policy=RemovalPolicy.RETAIN,
            description="Layer con dependencias comunes como boto3, requests, etc."
        )
