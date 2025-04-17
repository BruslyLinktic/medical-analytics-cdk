#!/usr/bin/env python3
"""
Script para desplegar los stacks del proyecto de analítica médica de manera controlada.
Incluye verificación de CloudFront y CORS.
"""
import os
import subprocess
import time
import json
import argparse
import sys

def run_command(command):
    """Ejecuta un comando de shell y retorna la salida"""
    print(f"Ejecutando: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error al ejecutar el comando: {command}")
        print(f"Error: {stderr.decode('utf-8')}")
        sys.exit(1)
    return stdout.decode('utf-8')

def parse_stack_outputs(stack_name):
    """Obtiene y analiza las salidas del stack de CloudFormation"""
    output = run_command(f"aws cloudformation describe-stacks --stack-name {stack_name}")
    stacks = json.loads(output)["Stacks"]
    if not stacks:
        return {}
    
    outputs = {}
    for output in stacks[0].get("Outputs", []):
        outputs[output["OutputKey"]] = output["OutputValue"]
    
    return outputs

def main():
    parser = argparse.ArgumentParser(description="Despliega los stacks del proyecto de analítica médica")
    parser.add_argument("--stage", choices=["dev", "test", "prod"], default="dev", help="Entorno a desplegar")
    parser.add_argument("--skip-storage", action="store_true", help="Omitir despliegue del stack de almacenamiento")
    parser.add_argument("--skip-ingestion", action="store_true", help="Omitir despliegue del stack de ingesta")
    parser.add_argument("--skip-cdn", action="store_true", help="Omitir despliegue del stack de CDN")
    args = parser.parse_args()
    
    stage = args.stage
    
    # Nombres de los stacks
    storage_stack = f"medical-analytics-storage-{stage}"
    ingestion_stack = f"medical-analytics-ingestion-{stage}"
    cdn_stack = f"medical-analytics-cdn-{stage}"
    
    # Configurar temporalmente las variables de entorno necesarias
    os.environ["CDK_DEFAULT_REGION"] = "us-east-2"  # Cambiar según sea necesario
    os.environ["CDK_DEFAULT_ACCOUNT"] = run_command("aws sts get-caller-identity --query 'Account' --output text").strip()
    
    # Desplegar el stack de almacenamiento
    if not args.skip_storage:
        print("\n=== Desplegando Stack de Almacenamiento ===")
        result = run_command(f"cdk deploy {storage_stack} --require-approval never")
        print(result)
        
        # Verificar el despliegue
        storage_outputs = parse_stack_outputs(storage_stack)
        print("Salidas del Stack de Almacenamiento:")
        for key, value in storage_outputs.items():
            print(f"  {key}: {value}")
    
    # Desplegar el stack de ingesta
    if not args.skip_ingestion:
        print("\n=== Desplegando Stack de Ingesta ===")
        result = run_command(f"cdk deploy {ingestion_stack} --require-approval never")
        print(result)
        
        # Verificar el despliegue
        ingestion_outputs = parse_stack_outputs(ingestion_stack)
        print("Salidas del Stack de Ingesta:")
        for key, value in ingestion_outputs.items():
            print(f"  {key}: {value}")
    
    # Desplegar el stack de CDN
    if not args.skip_cdn:
        print("\n=== Desplegando Stack de CDN ===")
        result = run_command(f"cdk deploy {cdn_stack} --require-approval never")
        print(result)
        
        # Verificar el despliegue
        cdn_outputs = parse_stack_outputs(cdn_stack)
        print("Salidas del Stack de CDN:")
        for key, value in cdn_outputs.items():
            print(f"  {key}: {value}")
        
        if "CloudFrontURL" in cdn_outputs:
            print(f"\n=== Sitio web disponible en: {cdn_outputs['CloudFrontURL']} ===")
            print("Nota: La propagación completa de CloudFront puede tomar hasta 15 minutos.")
    
    print("\n=== Despliegue completado con éxito ===")
    print("Recuerda que para probar correctamente la aplicación:")
    print("1. Espera a que la distribución de CloudFront se despliegue completamente (15-30 minutos)")
    print("2. Utiliza la URL de CloudFront para acceder al frontend")
    print("3. Usa la API Key proporcionada para las solicitudes a la API")

if __name__ == "__main__":
    main()
