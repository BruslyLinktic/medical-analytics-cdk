#!/usr/bin/env python3
"""
Script simplificado para desplegar los stacks del proyecto de analítica médica.
Resuelve los problemas de dependencias cíclicas y configuración CORS.
"""
import subprocess
import sys
import os
import json
import time

def run_command(command):
    """Ejecuta un comando de shell y retorna la salida"""
    print(f"\n=== Ejecutando: {command} ===")
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Mostrar salida en tiempo real
    print(process.stdout)
    
    if process.returncode != 0:
        print(f"Error al ejecutar el comando: {command}")
        print(f"Error: {process.stderr}")
        return False
    return process.stdout

def get_stack_output(stack_name, output_key):
    """Obtiene un valor específico de las salidas del stack"""
    try:
        command = f"aws cloudformation describe-stacks --stack-name {stack_name} --query \"Stacks[0].Outputs[?OutputKey=='{output_key}'].OutputValue\" --output text"
        result = run_command(command)
        if not result:
            return None
        return result.strip()
    except Exception as e:
        print(f"Error al obtener salida del stack {stack_name}: {str(e)}")
        return None

def main():
    # Verificar si hay un stack de almacenamiento existente
    print("Verificando si ya existe el bucket S3...")
    result = run_command("aws s3 ls")
    bucket_exists = result and "medical-analytics-project-dev" in result
    
    if bucket_exists:
        print("\n⚠️ ADVERTENCIA: El bucket 'medical-analytics-project-dev' ya existe.")
        choice = input("¿Desea eliminarlo y crear uno nuevo? (s/n): ").lower()
        
        if choice == 's':
            print("Eliminando bucket existente...")
            run_command("aws s3 rb s3://medical-analytics-project-dev --force")
        else:
            print("Para continuar, modifique el nombre del bucket en storage_stack.py y vuelva a intentarlo.")
            sys.exit(1)
    
    # Sintetizar los stacks para asegurarse de que no hay errores
    print("\n=== Sintetizando stacks para verificar que no hay errores ===")
    if not run_command("cdk synth"):
        print("❌ Error al sintetizar los stacks. Corrija los errores antes de continuar.")
        sys.exit(1)
    
    # Desplegar stacks uno por uno
    print("\n=== Desplegando stack de almacenamiento ===")
    if not run_command("cdk deploy medical-analytics-storage-dev --require-approval never"):
        sys.exit(1)
    
    print("\n=== Desplegando stack de ingesta ===")
    if not run_command("cdk deploy medical-analytics-ingestion-dev --require-approval never"):
        sys.exit(1)
    
    print("\n=== Desplegando stack de CDN ===")
    if not run_command("cdk deploy medical-analytics-cdn-dev --require-approval never"):
        sys.exit(1)
    
    # Obtener información sobre los recursos desplegados
    api_url = get_stack_output("medical-analytics-ingestion-dev", "ApiEndpoint")
    api_key = get_stack_output("medical-analytics-ingestion-dev", "ApiKeyValue")
    cloudfront_url = get_stack_output("medical-analytics-cdn-dev", "CloudFrontURL")
    
    print("\n=== 🎉 Despliegue completado con éxito! ===")
    print("\nRecursos disponibles:")
    print(f"- API Gateway: {api_url}")
    print(f"- API Key: {api_key}")
    print(f"- Frontend (CloudFront): {cloudfront_url}")
    
    print("\n⚠️ IMPORTANTE:")
    print("1. La distribución de CloudFront puede tardar hasta 15-30 minutos en propagarse completamente.")
    print("2. Utiliza la URL de CloudFront para acceder al frontend.")
    print("3. La API Key ya está configurada en el frontend automáticamente.")
    
    # Probar la URL de CloudFront
    print("\n=== Verificando si CloudFront está listo ===")
    print("Esto puede tomar tiempo. Haremos una prueba inicial...")
    
    cf_command = f"curl -s -o /dev/null -w '%{{http_code}}' {cloudfront_url}"
    result = run_command(cf_command)
    
    if result and result.strip() in ['200', '301', '302', '307', '308']:
        print(f"✅ CloudFront responde correctamente: {result}")
    else:
        print("⚠️ CloudFront aún no está listo. Esto es normal, puede tardar hasta 30 minutos.")
        print(f"  Intente acceder manualmente a: {cloudfront_url} después de unos minutos.")
    
    # Sugerir probar CORS
    print("\n=== Prueba de CORS ===")
    print("Para verificar que CORS está configurado correctamente, puede ejecutar:")
    print(f"python test_cors.py {api_url}upload --api-key {api_key}")
    
    print("\n=== Despliegue finalizado ===")

if __name__ == "__main__":
    main()
