"""
网络爬虫技能集
提供网页抓取、数据提取等功能
"""

import requests
from urllib.parse import urljoin, urlparse
import re


class WebScraping:
    """网络爬虫工具类"""
    
    @staticmethod
    def fetch_url(url, timeout=10):
        """获取URL内容"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            return f"Error fetching URL: {e}"
    
    @staticmethod
    def fetch_json(url, timeout=10):
        """获取JSON数据"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return f"Error fetching JSON: {e}"
    
    @staticmethod
    def download_file(url, save_path, timeout=30):
        """下载文件"""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except requests.RequestException as e:
            return f"Error downloading file: {e}"
    
    @staticmethod
    def extract_links(html, base_url=None):
        """提取HTML中的链接"""
        pattern = r'href=["\'](.*?)["\']'
        links = re.findall(pattern, html)
        
        if base_url:
            links = [urljoin(base_url, link) for link in links]
        
        return links
    
    @staticmethod
    def extract_images(html, base_url=None):
        """提取HTML中的图片"""
        pattern = r'src=["\'](.*?\.(?:jpg|jpeg|png|gif|webp))["\']'
        images = re.findall(pattern, html, re.IGNORECASE)
        
        if base_url:
            images = [urljoin(base_url, img) for img in images]
        
        return images
    
    @staticmethod
    def is_valid_url(url):
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def get_domain(url):
        """获取域名"""
        parsed = urlparse(url)
        return parsed.netloc
