#!/usr/bin/env python3
"""
CSV处理器 - 改进的CSV解析功能
"""
import csv
import io
import re
from typing import List, Tuple, Optional

class CSVProcessor:
    """CSV处理器"""
    
    @staticmethod
    def parse_csv(csv_content: str) -> List[Tuple[str, int]]:
        """
        解析CSV内容，提取IP和端口
        
        Args:
            csv_content: CSV文件内容
            
        Returns:
            List[Tuple[str, int]]: IP和端口列表
        """
        if not csv_content.strip():
            return []
        
        ip_port_pairs = []
        
        # 方法1: 尝试标准CSV解析
        try:
            # 尝试检测编码
            lines = csv_content.splitlines()
            
            # 尝试不同的分隔符
            for delimiter in [',', ';', '\t', ' ']:
                try:
                    reader = csv.reader(io.StringIO(csv_content), delimiter=delimiter)
                    for row in reader:
                        if not row:
                            continue
                        
                        # 尝试从行中提取IP和端口
                        ip, port = CSVProcessor._extract_ip_port_from_row(row)
                        if ip:
                            ip_port_pairs.append((ip, port))
                    
                    if ip_port_pairs:
                        print(f"✅ 使用分隔符 '{delimiter}' 成功解析CSV")
                        break
                except:
                    continue
        
        except Exception as e:
            print(f"⚠️ CSV标准解析失败: {e}")
        
        # 方法2: 如果标准解析失败，使用正则表达式
        if not ip_port_pairs:
            ip_port_pairs = CSVProcessor._extract_with_regex(csv_content)
        
        # 去重
        unique_pairs = []
        seen = set()
        for ip, port in ip_port_pairs:
            key = f"{ip}:{port}"
            if key not in seen:
                seen.add(key)
                unique_pairs.append((ip, port))
        
        print(f"📊 从CSV中提取到 {len(unique_pairs)} 个IP:端口对")
        if unique_pairs:
            print(f"示例: {unique_pairs[0]}")
        
        return unique_pairs
    
    @staticmethod
    def _extract_ip_port_from_row(row: List[str]) -> Tuple[Optional[str], Optional[int]]:
        """从CSV行中提取IP和端口"""
        from config import config
        
        ip = None
        port = None
        
        for cell in row:
            if not cell or not isinstance(cell, str):
                continue
            
            cell = cell.strip()
            
            # 检查是否是 IP:端口 格式
            if ':' in cell:
                parts = cell.split(':')
                if len(parts) == 2:
                    potential_ip = parts[0].strip()
                    potential_port = parts[1].strip()
                    
                    if CSVProcessor._is_valid_ip(potential_ip):
                        ip = potential_ip
                        try:
                            port_int = int(potential_port)
                            if 1 <= port_int <= 65535:
                                port = port_int
                        except:
                            pass
                    
                    if ip and port:
                        return ip, port
            
            # 检查是否是独立IP
            if CSVProcessor._is_valid_ip(cell):
                ip = cell
            
            # 检查是否是独立端口
            try:
                port_int = int(cell)
                if 1 <= port_int <= 65535:
                    port = port_int
            except:
                pass
        
        # 如果没有找到端口，使用默认端口
        if ip and not port:
            port = config.DEFAULT_PORT
        
        return ip, port
    
    @staticmethod
    def _extract_with_regex(text: str) -> List[Tuple[str, int]]:
        """使用正则表达式从文本中提取IP和端口"""
        from config import config
        
        ip_port_pairs = []
        
        # 匹配多种格式:
        # 1. IP:端口
        # 2. IP,端口
        # 3. IP 端口
        # 4. IP;端口
        
        # 替换常见分隔符为冒号，便于统一处理
        normalized = text.replace(',', ':').replace(';', ':').replace('\t', ':')
        normalized = re.sub(r'\s+', ':', normalized)
        
        # 匹配 IP:端口 格式
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
        matches = re.findall(pattern, normalized)
        
        for ip, port_str in matches:
            if CSVProcessor._is_valid_ip(ip):
                try:
                    port = int(port_str)
                    if 1 <= port <= 65535:
                        ip_port_pairs.append((ip, port))
                except:
                    continue
        
        # 如果还没有找到，尝试更宽松的匹配
        if not ip_port_pairs:
            # 匹配独立的IP地址
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ip_matches = re.findall(ip_pattern, text)
            
            for ip in ip_matches:
                if CSVProcessor._is_valid_ip(ip):
                    ip_port_pairs.append((ip, config.DEFAULT_PORT))
        
        return ip_port_pairs
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """验证IP地址有效性"""
        if not ip or not isinstance(ip, str):
            return False
        
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True