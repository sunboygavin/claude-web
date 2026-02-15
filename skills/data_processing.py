"""
数据处理技能集
提供JSON、CSV、数据转换等功能
"""

import json
import csv
from datetime import datetime


class DataProcessing:
    """数据处理工具类"""
    
    @staticmethod
    def read_json(file_path):
        """读取JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(file_path, data, indent=2):
        """写入JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def read_csv(file_path):
        """读取CSV文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    @staticmethod
    def write_csv(file_path, data, fieldnames=None):
        """写入CSV文件"""
        if not data:
            return
        
        if fieldnames is None:
            fieldnames = data[0].keys()
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def json_to_csv(json_file, csv_file):
        """JSON转CSV"""
        data = DataProcessing.read_json(json_file)
        DataProcessing.write_csv(csv_file, data)
    
    @staticmethod
    def csv_to_json(csv_file, json_file):
        """CSV转JSON"""
        data = DataProcessing.read_csv(csv_file)
        DataProcessing.write_json(json_file, data)
    
    @staticmethod
    def filter_data(data, key, value):
        """过滤数据"""
        return [item for item in data if item.get(key) == value]
    
    @staticmethod
    def sort_data(data, key, reverse=False):
        """排序数据"""
        return sorted(data, key=lambda x: x.get(key, ''), reverse=reverse)
    
    @staticmethod
    def group_by(data, key):
        """按键分组"""
        groups = {}
        for item in data:
            group_key = item.get(key)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
        return groups
    
    @staticmethod
    def merge_data(data1, data2, key):
        """合并数据"""
        merged = {item[key]: item for item in data1}
        for item in data2:
            if item[key] in merged:
                merged[item[key]].update(item)
            else:
                merged[item[key]] = item
        return list(merged.values())
