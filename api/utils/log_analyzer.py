"""
Utilidad para analizar archivos de log y detectar patrones de errores en GoolStar.

Este script proporciona funciones para analizar los registros de log
y detectar patrones, frecuencias de errores y problemas potenciales.
"""
import datetime
import logging
import re
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

        # Convertir error_sources a Counter para poder usar most_common
        error_sources_counter = Counter(results["error_sources"])

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
            for source, count in error_sources_counter.most_common(10)
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

    def detect_naive_datetimes(self, days_back=1):
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
        naive_datetimes = self.detect_naive_datetimes(days_back)

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

    def find_errors(self, days_back=1):
        """
        Encuentra errores en los logs.
        
        Args:
            days_back: Cuántos días hacia atrás analizar
            
        Returns:
            Diccionario con errores encontrados
        """
        results = {}
        for file in os.listdir(self.log_dir):
            if file.endswith('.log'):
                with open(self.log_dir / file, 'r') as f:
                    for line in f:
                        if self.error_pattern.search(line):
                            error_msg_match = re.search(r'ERROR.*?:(.*?)(?:\n|$)', line)
                            if error_msg_match:
                                error_msg = error_msg_match.group(1).strip()
                                if error_msg not in results:
                                    results[error_msg] = []
                                results[error_msg].append({
                                    "timestamp": self.datetime_pattern.search(line).group(1),
                                    "message": error_msg,
                                    "level": "ERROR"
                                })
        return results

    def find_pattern(self, pattern, days_back=1):
        """
        Busca un patrón específico en los logs.
        
        Args:
            pattern: Patrón a buscar
            days_back: Cuántos días hacia atrás analizar
            
        Returns:
            Lista de ocurrencias del patrón
        """
        results = []
        for file in os.listdir(self.log_dir):
            if file.endswith('.log'):
                with open(self.log_dir / file, 'r') as f:
                    for line in f:
                        if re.search(pattern, line):
                            datetime_match = self.datetime_pattern.search(line)
                            level_match = self.level_pattern.search(line)
                            results.append({
                                "timestamp": datetime_match.group(1) if datetime_match else "Unknown",
                                "message": line.strip(),
                                "level": level_match.group(1) if level_match else "Unknown"
                            })
        return results


if __name__ == "__main__":
    """
    Interfaz de línea de comandos para el analizador de logs.
    Ejemplos de uso:
        python -m api.utils.log_analyzer --days=7 --output=reporte.json
        python -m api.utils.log_analyzer --error-report --days=3
        python -m api.utils.log_analyzer --naive-datetime-check
        python -m api.utils.log_analyzer --pattern="Error al procesar" --days=14
    """
    import argparse
    import django
    import os
    import json
    import sys
    from datetime import datetime

    # Configurar Django si se ejecuta directamente
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goolstar_backend.settings')
    django.setup()

    # Parsear argumentos
    parser = argparse.ArgumentParser(description="Analizador de logs para GoolStar")
    parser.add_argument('--days', type=int, default=7, help='Número de días hacia atrás para analizar los logs')
    parser.add_argument('--output', type=str, help='Ruta del archivo para guardar el reporte (por defecto stdout)')
    parser.add_argument('--error-report', action='store_true', help='Generar reporte de errores')
    parser.add_argument('--naive-datetime-check', action='store_true',
                        help='Buscar problemas con fechas sin zona horaria')
    parser.add_argument('--pattern', type=str, help='Patrón de texto específico a buscar en los logs')
    parser.add_argument('--format', choices=['json', 'text'], default='json', help='Formato de salida')

    args = parser.parse_args()

    try:
        # Crear instancia del analizador
        analyzer = LogAnalyzer()

        # Decidir qué tipo de análisis realizar
        if args.naive_datetime_check:
            # Buscar problemas con fechas sin zona horaria
            print("Analizando problemas de fechas sin zona horaria...")
            results = analyzer.detect_naive_datetimes(days_back=args.days)

            if args.format == 'json':
                report = {
                    "naive_datetime_issues": [
                        {"timestamp": str(entry["timestamp"]),
                         "message": entry["message"],
                         "file": entry["file"],
                         "line": entry["line"]}
                        for entry in results
                    ],
                    "total_issues": len(results),
                    "analyzed_days": args.days,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                report = f"Problemas de fechas sin zona horaria (últimos {args.days} días):\n"
                report += f"Total encontrados: {len(results)}\n\n"
                for entry in results:
                    report += f"- {entry['timestamp']}: {entry['message']}\n"
                    report += f"  En archivo: {entry['file']} (línea {entry['line']})\n\n"

        elif args.error_report:
            # Generar reporte de errores
            print("Generando reporte de errores...")
            results = analyzer.find_errors(days_back=args.days)

            if args.format == 'json':
                report = {
                    "error_report": results,
                    "total_errors": sum(len(errors) for errors in results.values()),
                    "error_types": list(results.keys()),
                    "analyzed_days": args.days,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                report = f"Reporte de errores (últimos {args.days} días):\n"
                total_errors = sum(len(errors) for errors in results.values())
                report += f"Total de errores encontrados: {total_errors}\n\n"

                for error_type, errors in results.items():
                    report += f"Tipo de error: {error_type}\n"
                    report += f"Ocurrencias: {len(errors)}\n"
                    report += "Ejemplos:\n"

                    # Mostrar hasta 3 ejemplos por tipo
                    for idx, error in enumerate(errors[:3]):
                        report += f"  {idx + 1}. {error['message']}\n"
                        report += f"     Fecha: {error['timestamp']}\n"

                    report += "\n"

        elif args.pattern:
            # Buscar un patrón específico
            print(f"Buscando patrón '{args.pattern}'...")
            results = analyzer.find_pattern(args.pattern, days_back=args.days)

            if args.format == 'json':
                report = {
                    "pattern_matches": [
                        {"timestamp": str(entry["timestamp"]),
                         "message": entry["message"],
                         "level": entry["level"]}
                        for entry in results
                    ],
                    "total_matches": len(results),
                    "pattern": args.pattern,
                    "analyzed_days": args.days,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                report = f"Resultados para patrón '{args.pattern}' (últimos {args.days} días):\n"
                report += f"Total de coincidencias: {len(results)}\n\n"
                for entry in results:
                    report += f"- [{entry['level']}] {entry['timestamp']}: {entry['message']}\n"

        else:
            # Reporte general
            print("Generando reporte general...")
            results = analyzer.generate_report(days_back=args.days)

            if args.format == 'json':
                report = results
                # Añadir metadatos
                report["analyzed_days"] = args.days
                report["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                report = f"Reporte general de logs (últimos {args.days} días):\n"
                report += f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

                # Estadísticas por nivel
                report += "Estadísticas por nivel:\n"
                for level, count in results["summary"].items():
                    report += f"  {level}: {count} entradas\n"

                # Errores más frecuentes
                report += "\nErrores más frecuentes:\n"
                for error in results["file_analysis"]["error.log"]["common_errors"][:5]:  # Top 5
                    report += f"  - {error['error']} ({error['count']} ocurrencias)\n"

                # Problemas de zona horaria
                report += f"\nProblemas de zona horaria: {len(results['naive_datetimes'])} detectados\n"

        # Decidir dónde enviar la salida
        if args.output:
            with open(args.output, 'w') as f:
                if args.format == 'json':
                    json.dump(report, f, indent=2)
                else:
                    f.write(report)
            print(f"Reporte guardado en: {args.output}")
        else:
            # Imprimir a stdout
            if args.format == 'json':
                print(json.dumps(report, indent=2))
            else:
                print(report)

        sys.exit(0)

    except Exception as e:
        print(f"Error al ejecutar el analizador de logs: {str(e)}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
