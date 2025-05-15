"""
Utilidad para analizar archivos de log y detectar patrones de errores en GoolStar.

Este script proporciona funciones para analizar los registros de log
y detectar patrones, frecuencias de errores y problemas potenciales.
"""
import re
import json
import os
import datetime
import logging
from collections import Counter, defaultdict
from pathlib import Path

# Configurar logger para el propio analizador
logger = logging.getLogger('api.utils.log_analyzer')

class LogAnalyzer:
    """Clase para analizar logs de la aplicación GoolStar."""
    
    def __init__(self, log_dir=None):
        """
        Inicializa el analizador de logs.
        
        Args:
            log_dir: Directorio donde se encuentran los archivos de log.
                     Si es None, usa el directorio de logs predeterminado.
        """
        if log_dir is None:
            # Obtener el directorio de logs desde la configuración de Django
            from django.conf import settings
            self.log_dir = settings.LOGS_DIR
        else:
            self.log_dir = Path(log_dir)
        
        # Expresiones regulares para análisis
        self.datetime_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})')
        self.level_pattern = re.compile(r'\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\]')
        self.naive_dt_pattern = re.compile(r'Naive Datetime Detected')
        self.error_pattern = re.compile(r'ERROR|Exception|Error')
        
    def analyze_file(self, filename, days_back=1):
        """
        Analiza un archivo de log específico.
        
        Args:
            filename: Nombre del archivo a analizar (por ejemplo 'error.log')
            days_back: Cuántos días hacia atrás analizar
            
        Returns:
            Diccionario con estadísticas del análisis
        """
        filepath = self.log_dir / filename
        if not filepath.exists():
            logger.error(f"El archivo {filepath} no existe")
            return {"error": f"El archivo {filepath} no existe"}
        
        # Calcular la fecha límite
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        results = {
            "total_lines": 0,
            "error_count": 0,
            "warning_count": 0,
            "naive_datetime_count": 0,
            "common_errors": Counter(),
            "error_times": defaultdict(int),
            "error_sources": defaultdict(int)
        }
        
        with open(filepath, 'r') as file:
            for line in file:
                results["total_lines"] += 1
                
                # Extraer fecha/hora y verificar si está dentro del rango
                datetime_match = self.datetime_pattern.search(line)
                if datetime_match:
                    line_date = datetime_match.group(1).split()[0]
                    if line_date < cutoff_str:
                        continue
                
                # Contar por nivel de log
                level_match = self.level_pattern.search(line)
                if level_match:
                    level = level_match.group(1)
                    if level == "ERROR":
                        results["error_count"] += 1
                        
                        # Extraer hora para análisis temporal
                        if datetime_match:
                            hour = datetime_match.group(1).split()[1].split(':')[0]
                            results["error_times"][hour] += 1
                        
                        # Extraer fuente del error (módulo)
                        module_match = re.search(r'\[ERROR\] ([\w\.]+)', line)
                        if module_match:
                            module = module_match.group(1)
                            results["error_sources"][module] += 1
                        
                        # Extraer mensaje de error principal
                        error_msg_match = re.search(r'ERROR.*?:(.*?)(?:\n|$)', line)
                        if error_msg_match:
                            error_msg = error_msg_match.group(1).strip()
                            # Simplificar errores similares agrupando por patrón
                            simplified_error = re.sub(r'[0-9]+', 'N', error_msg)
                            simplified_error = re.sub(r'"[^"]*"', '"STR"', simplified_error)
                            results["common_errors"][simplified_error] += 1
                    
                    elif level == "WARNING":
                        results["warning_count"] += 1
                
                # Detectar problemas de zona horaria
                if self.naive_dt_pattern.search(line):
                    results["naive_datetime_count"] += 1
        
        # Convertir contadores en listas para JSON
        results["common_errors"] = [
            {"error": error, "count": count} 
            for error, count in results["common_errors"].most_common(10)
        ]
        results["error_times"] = [
            {"hour": hour, "count": count} 
            for hour, count in sorted(results["error_times"].items())
        ]
        results["error_sources"] = [
            {"source": source, "count": count} 
            for source, count in results["error_sources"].most_common(10)
        ]
        
        return results
    
    def analyze_all(self, days_back=1):
        """
        Analiza todos los archivos de log disponibles.
        
        Args:
            days_back: Cuántos días hacia atrás analizar
            
        Returns:
            Diccionario con resultados del análisis por archivo
        """
        results = {}
        for file in os.listdir(self.log_dir):
            if file.endswith('.log'):
                results[file] = self.analyze_file(file, days_back)
        return results
    
    def detect_naive_datetimes(self):
        """
        Detecta específicamente problemas de fechas sin zona horaria.
        
        Returns:
            Lista de ocurrencias de datetimes sin zona horaria
        """
        results = []
        debug_log = self.log_dir / 'debug.log'
        
        if not debug_log.exists():
            return {"error": "Archivo debug.log no encontrado"}
        
        with open(debug_log, 'r') as file:
            for line_num, line in enumerate(file, 1):
                if self.naive_dt_pattern.search(line):
                    # Extraer información relevante
                    datetime_match = self.datetime_pattern.search(line)
                    datetime_str = datetime_match.group(1) if datetime_match else "Unknown"
                    
                    # Extraer ubicación del problema
                    location_match = re.search(r'Location: (.*)', line)
                    location = location_match.group(1) if location_match else "Unknown"
                    
                    results.append({
                        "line": line_num,
                        "datetime": datetime_str,
                        "location": location,
                        "full_message": line.strip()
                    })
        
        return results

    def generate_report(self, days_back=1, output_file=None):
        """
        Genera un informe completo del análisis de logs.
        
        Args:
            days_back: Cuántos días hacia atrás analizar
            output_file: Si se especifica, guarda el reporte en este archivo
            
        Returns:
            Diccionario con el reporte completo
        """
        analysis = self.analyze_all(days_back)
        naive_datetimes = self.detect_naive_datetimes()
        
        report = {
            "generated_at": datetime.datetime.now().isoformat(),
            "period_analyzed": f"Últimos {days_back} días",
            "file_analysis": analysis,
            "naive_datetimes": naive_datetimes,
            "summary": {
                "total_errors": sum(a.get("error_count", 0) for a in analysis.values()),
                "total_warnings": sum(a.get("warning_count", 0) for a in analysis.values()),
                "total_naive_datetimes": len(naive_datetimes),
            }
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report


if __name__ == "__main__":
    # Uso desde línea de comandos
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Analizador de logs para GoolStar")
    parser.add_argument("--days", type=int, default=1, help="Días hacia atrás a analizar")
    parser.add_argument("--output", help="Archivo para guardar el reporte (formato JSON)")
    parser.add_argument("--check-naive", action="store_true", help="Solo verificar fechas sin zona horaria")
    args = parser.parse_args()
    
    # Configurar Django para poder importar settings
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goolstar_backend.settings')
    django.setup()
    
    analyzer = LogAnalyzer()
    
    if args.check_naive:
        results = analyzer.detect_naive_datetimes()
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(json.dumps(results, indent=2))
    else:
        report = analyzer.generate_report(args.days, args.output)
        if not args.output:
            print(json.dumps(report, indent=2))
