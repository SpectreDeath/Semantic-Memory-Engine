"""
Monitoring & Diagnostics Tools
Performance profiler, database health checker, cache efficiency analyzer.
"""

from mcp.server.fastmcp import FastMCP
import psutil
import os
import json
import sqlite3
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

mcp = FastMCP("MonitoringDiagnostics")

DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")
LOG_DIR = os.path.normpath("D:/mcp_servers/logs")

class PerformanceProfiler:
    """Profiles system performance for 1660 Ti and CPU."""
    
    @staticmethod
    def profile_system() -> Dict[str, Any]:
        """Profiles current system performance."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage(os.path.dirname(DB_PATH))
            
            # Process metrics
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            profile = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'core_count': cpu_count,
                    'status': 'normal' if cpu_percent < 80 else 'high'
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent_used': memory.percent,
                    'status': 'normal' if memory.percent < 80 else 'warning'
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'percent_used': disk.percent,
                    'status': 'normal' if disk.percent < 80 else 'warning'
                },
                'process': {
                    'rss_mb': process_memory.rss / (1024**2),
                    'vms_mb': process_memory.vms / (1024**2),
                    'status': 'normal'
                }
            }
            
            return profile
        
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def profile_gpu_fallback() -> Dict[str, Any]:
        """GPU monitoring (1660 Ti) with fallback if pynvml unavailable."""
        try:
            import pynvml
            pynvml.nvmlInit()
            
            device_count = pynvml.nvmlDeviceGetCount()
            gpus = []
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                gpus.append({
                    'device_id': i,
                    'memory_total_mb': mem.total / (1024**2),
                    'memory_free_mb': mem.free / (1024**2),
                    'memory_used_mb': mem.used / (1024**2),
                    'gpu_util_percent': util.gpu,
                    'memory_util_percent': util.memory
                })
            
            pynvml.nvmlShutdown()
            return {'gpus': gpus, 'count': device_count}
        
        except:
            return {'gpus': [], 'error': 'GPU monitoring not available', 'note': 'Install pynvml for NVIDIA GPU monitoring'}


class DatabaseHealthChecker:
    """Checks database health and integrity."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Checks database health."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            health = {
                'database': DB_PATH,
                'status': 'accessible',
                'tables': [],
                'total_records': 0,
                'db_file_size_mb': os.path.getsize(DB_PATH) / (1024**2) if os.path.exists(DB_PATH) else 0,
                'integrity': 'good'
            }
            
            # Check each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                health['tables'].append({
                    'name': table_name,
                    'row_count': count,
                    'status': 'active'
                })
                
                health['total_records'] += count
            
            # Check database integrity
            try:
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                if integrity_result and integrity_result[0] == 'ok':
                    health['integrity'] = 'good'
                else:
                    health['integrity'] = 'issues_detected'
            except:
                pass
            
            conn.close()
            
            return health
        
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
    
    @staticmethod
    def optimize_database() -> Dict[str, Any]:
        """Optimizes database performance."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Run optimization commands
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            cursor.execute("PRAGMA optimize")
            
            conn.commit()
            conn.close()
            
            return {
                'status': 'optimized',
                'operations': ['VACUUM', 'ANALYZE', 'PRAGMA optimize'],
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}


class CacheEfficiencyAnalyzer:
    """Analyzes cache and retrieval efficiency."""
    
    @staticmethod
    def analyze_retrieval_efficiency() -> Dict[str, Any]:
        """Analyzes how efficiently we're retrieving cached data."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get sentiment log statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT source_file) as unique_files,
                    AVG(compound) as avg_sentiment,
                    MIN(timestamp) as oldest_record,
                    MAX(timestamp) as newest_record
                FROM sentiment_logs
            ''')
            
            result = cursor.fetchone()
            
            efficiency = {
                'cache_metrics': {
                    'total_cached_records': result[0] if result[0] else 0,
                    'unique_files_cached': result[1] if result[1] else 0,
                    'avg_sentiment': round(result[2] or 0, 4),
                    'cache_span_days': f"{result[2]} - {result[3]}" if result[2] and result[3] else 'N/A'
                },
                'efficiency_score': 0.0,
                'recommendations': []
            }
            
            # Calculate efficiency score
            if result[0] and result[0] > 100:
                efficiency['efficiency_score'] += 0.5
                efficiency['recommendations'].append('Cache has good coverage')
            
            if result[1] and result[1] > 10:
                efficiency['efficiency_score'] += 0.3
                efficiency['recommendations'].append('Multiple data sources indexed')
            
            if result[0] and result[1] and (result[0] / result[1]) > 10:
                efficiency['efficiency_score'] += 0.2
                efficiency['recommendations'].append('Good record density per source')
            
            efficiency['efficiency_score'] = min(efficiency['efficiency_score'], 1.0)
            
            conn.close()
            
            return efficiency
        
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def analyze_log_performance() -> Dict[str, Any]:
        """Analyzes log file performance."""
        try:
            log_files = []
            total_size = 0
            
            if os.path.exists(LOG_DIR):
                for file in os.listdir(LOG_DIR):
                    file_path = os.path.join(LOG_DIR, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        log_files.append({
                            'name': file,
                            'size_kb': size / 1024,
                            'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                        })
                        total_size += size
            
            return {
                'log_directory': LOG_DIR,
                'total_log_size_mb': total_size / (1024**2),
                'log_file_count': len(log_files),
                'log_files': log_files,
                'status': 'analyzed'
            }
        
        except Exception as e:
            return {'error': str(e)}


@mcp.tool()
def profile_system_performance() -> str:
    """
    Profiles current system performance.
    Returns CPU, memory, disk, and process metrics.
    """
    try:
        profiler = PerformanceProfiler()
        cpu_mem_disk = profiler.profile_system()
        gpu_info = profiler.profile_gpu_fallback()
        
        result = {
            'system_profile': cpu_mem_disk,
            'gpu_info': gpu_info,
            'timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def check_database_health() -> str:
    """
    Checks database health, integrity, and row counts.
    Identifies potential issues with data storage.
    """
    try:
        checker = DatabaseHealthChecker()
        result = checker.check_database()
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def optimize_database_performance() -> str:
    """
    Optimizes database: VACUUM, ANALYZE, PRAGMA optimize.
    Run periodically to maintain performance.
    """
    try:
        checker = DatabaseHealthChecker()
        result = checker.optimize_database()
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def analyze_cache_efficiency() -> str:
    """
    Analyzes cache efficiency and retrieval performance.
    Returns recommendations for optimization.
    """
    try:
        analyzer = CacheEfficiencyAnalyzer()
        result = analyzer.analyze_retrieval_efficiency()
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def analyze_log_performance() -> str:
    """
    Analyzes log file directory performance and size.
    Helps identify if logs need cleanup.
    """
    try:
        analyzer = CacheEfficiencyAnalyzer()
        result = analyzer.analyze_log_performance()
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
