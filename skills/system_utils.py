"""
系统工具技能集
提供系统信息、进程管理等功能
"""

import os
import sys
import platform
import psutil
from datetime import datetime


class SystemUtils:
    """系统工具类"""
    
    @staticmethod
    def get_system_info():
        """获取系统信息"""
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': sys.version
        }
    
    @staticmethod
    def get_cpu_info():
        """获取CPU信息"""
        return {
            'physical_cores': psutil.cpu_count(logical=False),
            'total_cores': psutil.cpu_count(logical=True),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    @staticmethod
    def get_memory_info():
        """获取内存信息"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent
        }
    
    @staticmethod
    def get_disk_info():
        """获取磁盘信息"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    
    @staticmethod
    def get_network_info():
        """获取网络信息"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    
    @staticmethod
    def list_processes():
        """列出进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
    
    @staticmethod
    def get_env_var(key, default=None):
        """获取环境变量"""
        return os.environ.get(key, default)
    
    @staticmethod
    def set_env_var(key, value):
        """设置环境变量"""
        os.environ[key] = value
    
    @staticmethod
    def get_current_time():
        """获取当前时间"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
