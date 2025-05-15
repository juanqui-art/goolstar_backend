#!/usr/bin/env python
"""
Script para probar la autenticación JWT implementada en la API GoolStar.
Permite probar:
1. Registro de nuevo usuario
2. Obtención de tokens
3. Acceso a endpoints protegidos
4. Refrescar tokens
"""

import requests
import json
import sys
import time
from pprint import pprint

API_BASE_URL = "http://127.0.0.1:8000/api"
TIMEOUT = 15  # segundos


def imprimir_separador():
    print("-" * 80)


def probar_registro(username, password, email):
    """Prueba el registro de un nuevo usuario"""
    print("\n1. PROBANDO REGISTRO DE USUARIO")
    imprimir_separador()
    
    url = f"{API_BASE_URL}/auth/registro/"
    data = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        response = requests.post(url, json=data, timeout=TIMEOUT)
        resultado = response.json()
        
        if response.status_code == 201:
            print(f"✅ Usuario creado exitosamente: {username}")
            print("Tokens obtenidos:")
            print(f"  - Access token: {resultado['access'][:20]}...")
            print(f"  - Refresh token: {resultado['refresh'][:20]}...")
            return resultado
        else:
            print(f"❌ Error al crear usuario: {response.status_code}")
            pprint(resultado)
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


def probar_autenticacion(username, password):
    """Prueba la obtención de tokens con credenciales existentes"""
    print("\n2. PROBANDO AUTENTICACIÓN")
    imprimir_separador()
    
    url = f"{API_BASE_URL}/auth/token/"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data, timeout=TIMEOUT)
        resultado = response.json()
        
        if response.status_code == 200:
            print(f"✅ Autenticación exitosa para: {username}")
            print("Tokens obtenidos:")
            print(f"  - Access token: {resultado['access'][:20]}...")
            print(f"  - Refresh token: {resultado['refresh'][:20]}...")
            print(f"  - User ID: {resultado.get('user_id')}")
            print(f"  - Email: {resultado.get('email')}")
            return resultado
        else:
            print(f"❌ Error de autenticación: {response.status_code}")
            pprint(resultado)
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


def probar_endpoint_protegido(access_token):
    """Prueba el acceso a un endpoint protegido usando el token JWT"""
    print("\n3. PROBANDO ENDPOINT PROTEGIDO")
    imprimir_separador()
    
    # Primero probamos sin autenticación (debería funcionar para GET)
    url = f"{API_BASE_URL}/torneos/"
    print(f"GET {url} (sin autenticación)")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            print(f"✅ Acceso de lectura sin autenticación correcto: {response.status_code}")
            resultado = response.json()
            print(f"   Total resultados: {resultado.get('count', 'N/A')}")
        else:
            print(f"❌ Error accediendo sin autenticación: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    
    # Ahora intentamos una operación POST (debe rechazarse sin token)
    print("\nPOST /api/categorias/ (sin autenticación)")
    data = {
        "nombre": "Categoría de Prueba JWT",
        "descripcion": "Esta categoría fue creada para probar JWT"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/categorias/", json=data, timeout=TIMEOUT)
        if response.status_code in [401, 403]:
            print(f"✅ POST sin autenticación correctamente rechazado: {response.status_code}")
        else:
            print(f"❓ Respuesta inesperada: {response.status_code}")
            pprint(response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    
    # Ahora intentamos con el token (debería funcionar)
    print("\nPOST /api/categorias/ (con token)")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/categorias/", 
                                json=data, 
                                headers=headers, 
                                timeout=TIMEOUT)
        resultado = response.json()
        
        if response.status_code == 201:
            print(f"✅ POST con token exitoso: {response.status_code}")
            print(f"   Categoría creada con ID: {resultado.get('id')}")
            return resultado
        else:
            print(f"❌ Error en POST con token: {response.status_code}")
            pprint(resultado)
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


def probar_refrescar_token(refresh_token):
    """Prueba el refresco de un token JWT"""
    print("\n4. PROBANDO REFRESCO DE TOKEN")
    imprimir_separador()
    
    url = f"{API_BASE_URL}/auth/token/refresh/"
    data = {
        "refresh": refresh_token
    }
    
    try:
        response = requests.post(url, json=data, timeout=TIMEOUT)
        # Imprimir información de depuración
        print(f"Status code: {response.status_code}")
        print(f"Respuesta: {response.text[:100]}")  # Mostrar primeros 100 caracteres
        
        if response.status_code == 200:
            resultado = response.json()
            print("✅ Token refrescado exitosamente")
            print(f"  - Nuevo access token: {resultado['access'][:20]}...")
            return resultado
        else:
            print(f"❌ Error al refrescar token: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None
    except ValueError as e:
        print(f"❌ Error al procesar la respuesta JSON: {e}")
        print(f"Respuesta del servidor: {response.text}")
        return None


def main():
    """Función principal que ejecuta todas las pruebas"""
    print("PRUEBA DE AUTENTICACIÓN JWT EN API GOOLSTAR")
    imprimir_separador()
    
    # Verifica que el servidor esté en ejecución
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: El servidor no está en ejecución o no es accesible.")
        print("   Ejecuta 'python manage.py runserver' e intenta de nuevo.")
        sys.exit(1)
    
    # Datos para las pruebas
    username = f"test_user_{int(time.time())}"  # Username único
    password = "password123"
    email = f"{username}@example.com"
    
    # 1. Registrar usuario
    registro = probar_registro(username, password, email)
    if not registro:
        print("\n❌ No se pudo continuar con las pruebas debido a errores en el registro.")
        return
    
    # Usar los tokens del registro
    access_token = registro['access']
    refresh_token = registro['refresh']
    
    # 2. Probar autenticación (opcional, ya tenemos tokens del registro)
    # autenticacion = probar_autenticacion(username, password)
    
    # 3. Probar acceso a endpoint protegido
    resultado_endpoint = probar_endpoint_protegido(access_token)
    
    # 4. Probar refresco de token
    nuevo_token = probar_refrescar_token(refresh_token)
    
    print("\nRESUMEN DE PRUEBAS")
    imprimir_separador()
    print(f"✓ Usuario creado: {username}")
    print(f"✓ Token obtenido correctamente")
    if resultado_endpoint:
        print(f"✓ Acceso a endpoint protegido exitoso")
    if nuevo_token:
        print(f"✓ Refresco de token exitoso")
    
    print("\n¡Pruebas completadas!")


if __name__ == "__main__":
    main()
