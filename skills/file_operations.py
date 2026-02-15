"""
文件操作技能集
提供常用的文件读写、搜索、批量处理功能
"""

import os
import shutil
from pathlib import Path
import json


class FileOperations:
    """文件操作工具类"""
    
    @staticmethod
    def read_file(file_path):
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_file(file_path, content):
        """写入文件内容"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def append_file(file_path, content):
        """追加内容到文件"""
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def copy_file(src, dst):
        """复制文件"""
        shutil.copy2(src, dst)
    
    @staticmethod
    def move_file(src, dst):
        """移动文件"""
        shutil.move(src, dst)
    
    @staticmethod
    def delete_file(file_path):
        """删除文件"""
        if os.path.exists(file_path):
            os.remove(file_path)
    
    @staticmethod
    def list_files(directory, pattern='*'):
        """列出目录下的文件"""
        return list(Path(directory).glob(pattern))
    
    @staticmethod
    def find_files(directory, extension):
        """查找特定扩展名的文件"""
        return list(Path(directory).rglob(f'*.{extension}'))
    
    @staticmethod
    def get_file_info(file_path):
        """获取文件信息"""
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'is_file': os.path.isfile(file_path),
            'is_dir': os.path.isdir(file_path)
        }
