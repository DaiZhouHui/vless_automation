"""
CSV文件处理器
"""
import re
import csv
import io
from typing import List, Tuple, Dict, Any

class CSVProcessor:
    """CSV处理器"""
    
    def parse_csv(self, csv_content: str) -> List[Tuple[str, int]]:
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
        
        try:
            # 尝试标准CSV解析
            reader = csv.reader(io.StringIO(csv_content))
            for row in reader:
                if not row:
                    continue
                
                # 尝试从行中提取IP和端口
                ip, port = self._extract_ip_port_from_row(row)
                if ip:
                    ip_port_pairs.append((ip, port))
        
        except Exception:
            # CSV解析失败，使用正则表达式提取
            ip_port_pairs = self._extract_with_regex(csv_content)
        
        # 去重
        unique_pairs = []
        seen = set()
        for ip, port in ip_port_pairs:
            key = f"{ip}:{port}"
            if key not in seen:
                seen.add(key)
                unique_pairs.append((ip, port))
        
        return unique_pairs
    
    def _extract_ip_port_from_row(self, row: List[str]) -> Tuple[str, int]:
        """从CSV行中提取IP和端口"""
        import re
        from config import config
        
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        port_pattern = r'\b(\d{1,5})\b'
        
        ip = ""
        port = config.DEFAULT_PORT
        
        for cell in row:
            if not cell:
                continue
            
            # 查找IP地址
            ip_match = re.search(ip_pattern, cell)
            if ip_match and not ip:
                ip = ip_match.group(0)
            
            # 查找端口 (在1-65535之间)
            port_matches = re.findall(port_pattern, cell)
            for port_str in port_matches:
                port_int = int(port_str)
                if 1 <= port_int <= 65535 and port == config.DEFAULT_PORT:
                    port = port_int
        
        return ip, port
    
    def _extract_with_regex(self, text: str) -> List[Tuple[str, int]]:
        """使用正则表达式从文本中提取IP和端口"""
        from config import config
        
        ip_port_pairs = []
        
        # 匹配 IP:端口 格式
        pattern1 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
        matches1 = re.findall(pattern1, text)
        
        for ip, port_str in matches1:
            if self._is_valid_ip(ip):
                port = int(port_str)
                if 1 <= port <= 65535:
                    ip_port_pairs.append((ip, port))
        
        # 匹配 IP 端口 格式 (空格分隔)
        pattern2 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\d{1,5})'
        matches2 = re.findall(pattern2, text)
        
        for ip, port_str in matches2:
            if self._is_valid_ip(ip):
                port = int(port_str)
                if 1 <= port <= 65535:
                    ip_port_pairs.append((ip, port))
        
        # 只匹配IP (使用默认端口)
        pattern3 = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        matches3 = re.findall(pattern3, text)
        
        for ip in matches3:
            if self._is_valid_ip(ip) and not any(ip == existing_ip for existing_ip, _ in ip_port_pairs):
                ip_port_pairs.append((ip, config.DEFAULT_PORT))
        
        return ip_port_pairs
    
    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址有效性"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
            if len(part) > 1 and part[0] == '0':
                return False
        
        return True