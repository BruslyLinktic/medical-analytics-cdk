from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_iam as iam
)
from constructs import Construct
import os
import tempfile

class CDNStack(Stack):
    """
    Stack para la implementación de CloudFront como CDN para la interfaz web de carga de archivos.
    Proporciona entrega rápida de contenido, HTTPS y configuración CORS adecuada.
    También se encarga de la creación y despliegue del frontend.
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        api_gateway_url: str,
        api_key_value: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Crear bucket S3 para el frontend
        website_bucket = self._create_frontend_bucket()
        
        # 2. Desplegar archivos del frontend
        self._deploy_frontend_files(website_bucket, api_gateway_url, api_key_value)
        
        # 3. Crear la distribución de CloudFront
        self.distribution = self._create_distribution(website_bucket, api_gateway_url)
        
        # Outputs
        CfnOutput(self, "CloudFrontDomainName", value=self.distribution.domain_name)
        CfnOutput(self, "CloudFrontURL", value=f"https://{self.distribution.domain_name}")
        CfnOutput(self, "FrontendBucket", value=website_bucket.bucket_name)

    def _create_frontend_bucket(self) -> s3.Bucket:
        """
        Crea el bucket S3 para el frontend.
        """
        return s3.Bucket(
            self, 
            "MedicalAnalyticsFrontendBucket",
            bucket_name="medical-analytics-frontend-dev",
            website_index_document="index.html",
            website_error_document="index.html",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Bloqueamos todo acceso público directo
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD],
                allowed_origins=["*"],
                allowed_headers=["*"],
                max_age=3000
            )]
        )
    
    def _deploy_frontend_files(self, bucket: s3.Bucket, api_url: str, api_key_value: str) -> None:
        """
        Despliega los archivos del frontend en el bucket S3.
        """
        # Leer el archivo index.html y reemplazar la URL de la API
        with open("frontend/index.html", "r") as file:
            html_content = file.read()
            
        # Reemplazar la URL de la API y la API key
        html_content = html_content.replace("{{API_ENDPOINT}}", f"{api_url}upload")
        html_content = html_content.replace("{{API_KEY}}", api_key_value)
        
        # Crear archivo temporal con la URL actualizada
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "index.html")
        
        with open(temp_file_path, "w") as file:
            file.write(html_content)
        
        # Desplegar frontend desde el directorio temporal
        s3deploy.BucketDeployment(
            self, 
            "DeployMedicalAnalyticsFrontend",
            sources=[s3deploy.Source.asset(temp_dir)],
            destination_bucket=bucket
        )

    def _create_distribution(self, frontend_bucket: s3.Bucket, api_gateway_url: str) -> cloudfront.Distribution:
        """
        Crea una distribución CloudFront y la configura para servir el frontend
        y permitir CORS adecuadamente.
        """
        # Política de caché para el frontend
        frontend_cache_policy = cloudfront.CachePolicy(
            self,
            "FrontendCachePolicy",
            cache_policy_name="medical-analytics-frontend-cache",
            comment="Cache policy for Medical Analytics Frontend",
            default_ttl=Duration.days(1),
            min_ttl=Duration.minutes(1),
            max_ttl=Duration.days(1),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )

        # Política de solicitud de origen para CORS
        cors_origin_request_policy = cloudfront.OriginRequestPolicy(
            self,
            "CORSOriginRequestPolicy",
            origin_request_policy_name="medical-analytics-cors-policy",
            comment="Policy to forward CORS headers to origin",
            cookie_behavior=cloudfront.OriginRequestCookieBehavior.none(),
            header_behavior=cloudfront.OriginRequestHeaderBehavior.allow_list(
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers"
            ),
            query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.all()
        )

        # Política de respuesta para CORS
        cors_response_policy = cloudfront.ResponseHeadersPolicy(
            self,
            "CORSResponsePolicy",
            response_headers_policy_name="medical-analytics-cors-response",
            comment="Policy to add CORS headers to responses",
            cors_behavior=cloudfront.ResponseHeadersCorsBehavior(
                access_control_allow_credentials=True,
                access_control_allow_headers=["Authorization", "Content-Type", "X-Api-Key", "Origin", "Accept"],
                access_control_allow_methods=["GET", "POST", "OPTIONS"],
                access_control_allow_origins=["http://localhost:3000", "https://medical-analytics-frontend-dev.s3-website.us-east-1.amazonaws.com"],
                access_control_max_age=Duration.seconds(600),
                origin_override=True
            )
        )

        # Crear OAI (Origin Access Identity) para acceder al bucket S3
        oai = cloudfront.OriginAccessIdentity(
            self,
            "MedicalAnalyticsOAI",
            comment="OAI for Medical Analytics Frontend"
        )

        # Permitir acceso desde CloudFront usando policy (más explícito)
        # Primero, añadimos el permiso usando PolicyStatement que incluye el S3CanonicalUserId del OAI
        frontend_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[frontend_bucket.arn_for_objects("*")],
                principals=[iam.CanonicalUserPrincipal(
                    oai.cloud_front_origin_access_identity_s3_canonical_user_id
                )]
            )
        )
        
        # Segundo, añadimos un permiso usando el servicio principal de CloudFront
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
        
        # También usar grant_read como respaldo
        frontend_bucket.grant_read(iam.CanonicalUserPrincipal(
            oai.cloud_front_origin_access_identity_s3_canonical_user_id
        ))

        # Crear distribución CloudFront
        distribution = cloudfront.Distribution(
            self,
            "MedicalAnalyticsDistribution",
            default_root_object="index.html",  # Importante: especificar objeto raíz
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    frontend_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=frontend_cache_policy,
                response_headers_policy=cors_response_policy,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                origin_request_policy=cors_origin_request_policy,
            ),
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30)
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30)
                )
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # Solo Norte América y Europa para reducir costos
            enabled=True,
            comment="Distribution for Medical Analytics Frontend"
        )

        return distribution
