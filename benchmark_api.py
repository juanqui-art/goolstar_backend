import os
import time
import requests
import statistics

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goolstar_backend.settings')

# URLs a probar
ENDPOINTS = [
    'http://127.0.0.1:8000/api/partidos/proximos/',
    'http://127.0.0.1:8000/api/torneos/activos/',
    'http://127.0.0.1:8000/api/torneos/1/jugadores_destacados/',
    'http://127.0.0.1:8000/api/torneos/1/tabla_posiciones/',
]

def benchmark_endpoint(url, num_requests=5):
    """Realiza varias solicitudes a un endpoint y mide el tiempo de respuesta."""
    times = []
    for i in range(num_requests):
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        
        times.append(end_time - start_time)
        
        # Verificar si la respuesta fue exitosa
        if response.status_code != 200:
            print(f"Error en {url}: {response.status_code}")
            return None
            
    return {
        'url': url,
        'avg_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'median_time': statistics.median(times)
    }

def main():
    print("Realizando benchmark de la API GoolStar...\n")
    
    results = []
    for endpoint in ENDPOINTS:
        print(f"Probando {endpoint}...")
        result = benchmark_endpoint(endpoint)
        if result:
            results.append(result)
        print()
        
    # Mostrar resultados
    print("\nResultados del benchmark:")
    print("-" * 80)
    print(f"{'Endpoint':<50} {'Promedio (s)':<15} {'Mínimo (s)':<15} {'Máximo (s)':<15}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['url']:<50} {result['avg_time']:<15.4f} {result['min_time']:<15.4f} {result['max_time']:<15.4f}")

if __name__ == "__main__":
    main()
