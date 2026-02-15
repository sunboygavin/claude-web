"""
文本处理技能集
提供文本分析、格式化、转换等功能
"""

import re
from collections import Counter


class TextProcessing:
    """文本处理工具类"""
    
    @staticmethod
    def word_count(text):
        """统计单词数量"""
        words = re.findall(r'\w+', text.lower())
        return len(words)
    
    @staticmethod
    def char_count(text):
        """统计字符数量"""
        return len(text)
    
    @staticmethod
    def line_count(text):
        """统计行数"""
        return len(text.splitlines())
    
    @staticmethod
    def word_frequency(text, top_n=10):
        """统计词频"""
        words = re.findall(r'\w+', text.lower())
        return Counter(words).most_common(top_n)
    
    @staticmethod
    def remove_duplicates(text):
        """删除重复行"""
        lines = text.splitlines()
        unique_lines = list(dict.fromkeys(lines))
        return '\n'.join(unique_lines)
    
    @staticmethod
    def find_and_replace(text, find, replace):
        """查找并替换"""
        return text.replace(find, replace)
    
    @staticmethod
    def extract_emails(text):
        """提取邮箱地址"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    @staticmethod
    def extract_urls(text):
        """提取URL"""
        pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(pattern, text)
    
    @staticmethod
    def clean_whitespace(text):
        """清理多余空白"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def to_title_case(text):
        """转换为标题格式"""
        return text.title()
    
    @staticmethod
    def to_snake_case(text):
        """转换为蛇形命名"""
        text = re.sub(r'[\s-]+', '_', text)
        text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', text)
        text = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', text)
        return text.lower()
    
    @staticmethod
    def to_camel_case(text):
        """转换为驼峰命名"""
        words = re.split(r'[\s_-]+', text)
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
