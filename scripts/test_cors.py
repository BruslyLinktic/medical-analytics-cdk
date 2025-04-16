#!/usr/bin/env python3
"""
Script para probar la configuración CORS de la API.
Ejecuta una solicitud OPTIONS y verifica las cabeceras de respuesta.
"""
import argparse
import requests
import sys
import json

def test_cors(api_url):
    """
    Prueba la configuración CORS de una API enviando una solicitud OPTIONS
    y verificando las cabeceras de respuesta.
    """
    print(f"Probando CORS para la API en: {api_url}")
    
    # Hacer solicitud OPTIONS para probar CORS preflight
    try:
        response = requests.options(
            api_url,
            headers={
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,X-Api-Key'
            }
        )
        
        # Verificar código de estado
        print(f"Código de estado: {response.status_code}")
        if response.status_code != 200:
            print("ERROR: La solicitud OPTIONS no devolvió código 200")
            return False
        
        # Verificar cabeceras CORS
        headers = response.headers
        print("\nCabeceras de respuesta:")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        
        # Verificar cabeceras específicas de CORS
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers',
            'Access-Control-Allow-Credentials'
        ]
        
        missing_headers = [h for h in cors_headers if h not in headers]
        
        if missing_headers:
            print("\nERROR: Faltan las siguientes cabeceras CORS:")
            for h in missing_headers:
                print(f"  - {h}")
            return False
        
        # Verificar valores específicos
        if headers.get('Access-Control-Allow-Origin') != '*' and headers.get('Access-Control-Allow-Origin') != 'https://example.com':
            print("\nERROR: Access-Control-Allow-Origin no permite el origen de prueba")
            return False
        
        if 'POST' not in headers.get('Access-Control-Allow-Methods', ''):
            print("\nERROR: Access-Control-Allow-Methods no incluye POST")
            return False
        
        print("\nResumen de prueba CORS:")
        print("✅ La API está configurada correctamente para CORS")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\nERROR al conectar con la API: {e}")
        return False

def test_api_key(api_url, api_key):
    """
    Prueba la autenticación con API Key enviando una solicitud POST
    simple y verificando la respuesta.
    """
    print(f"\nProbando autenticación con API Key en: {api_url}")
    
    try:
        # Crear un payload mínimo para probar
        payload = {
            "test": True,
            "message": "API Key test"
        }
        
        # Hacer solicitud POST con la API Key
        response = requests.post(
            api_url,
            headers={
                'Content-Type': 'application/json',
                'X-Api-Key': api_key
            },
            json=payload
        )
        
        # Verificar código de estado
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        
        # La respuesta específica dependerá de la implementación del backend
        # pero al menos debería aceptar la solicitud (no 403/401)
        if response.status_code in [401, 403]:
            print("ERROR: La API Key fue rechazada")
            return False
            
        print("\nResumen de prueba de API Key:")
        print("✅ La API Key fue aceptada correctamente")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\nERROR al conectar con la API: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Prueba la configuración CORS de una API")
    parser.add_argument("api_url", help="URL de la API a probar (incluyendo el path '/upload')")
    parser.add_argument("--api-key", help="API Key para probar autenticación")
    args = parser.parse_args()
    
    # Normalizar URL
    api_url = args.api_url
    if not api_url.startswith('http'):
        api_url = f"https://{api_url}"
    
    # Probar CORS
    cors_ok = test_cors(api_url)
    
    # Probar API Key si se proporciona
    api_key_ok = True
    if args.api_key:
        api_key_ok = test_api_key(api_url, args.api_key)
    
    # Resumen final
    print("\n=== Resumen final de pruebas ===")
    print(f"CORS: {'✅ OK' if cors_ok else '❌ Error'}")
    if args.api_key:
        print(f"API Key: {'✅ OK' if api_key_ok else '❌ Error'}")
    
    if not cors_ok or (args.api_key and not api_key_ok):
        sys.exit(1)

if __name__ == "__main__":
    main()
