"""
节点管理器
"""
import re
from typing import List, Set
from datetime import datetime, timedelta
from config import config

class NodeManager:
    """节点管理器"""
    
    def __init__(self, config):
        self.config = config
    
    def merge_nodes(self, local_nodes: List[str], remote_nodes: List[str]) -> List[str]:
        """
        合并本地和远程节点，并去重
        
        Args:
            local_nodes: 本地节点
            remote_nodes: 远程节点
            
        Returns:
            List[str]: 合并去重后的节点
        """
        all_nodes = local_nodes + remote_nodes
        unique_nodes = []
        seen = set()
        
        for node in all_nodes:
            # 提取IP和端口作为唯一标识
            key = self._extract_ip_port_key(node)
            if key and key not in seen:
                seen.add(key)
                unique_nodes.append(node)
        
        return unique_nodes
    
    def filter_nodes_by_age(self, nodes: List[str]) -> List[str]:
        """
        根据节点创建日期过滤节点，只保留最近N天的
        
        Args:
            nodes: 节点列表
            
        Returns:
            List[str]: 过滤后的节点
        """
        if not config.AUTO_DELETE_OLD_NODES:
            return nodes
        
        filtered_nodes = []
        cutoff_date = datetime.now() - timedelta(days=config.MAX_DAYS_TO_KEEP)
        
        for node in nodes:
            node_date = self._extract_date_from_node(node)
            if node_date and node_date >= cutoff_date:
                filtered_nodes.append(node)
            elif not node_date:
                # 无法提取日期的节点保留
                filtered_nodes.append(node)
        
        return filtered_nodes
    
    def _extract_ip_port_key(self, node: str) -> Optional[str]:
        """从节点中提取IP:端口作为唯一键"""
        try:
            # 匹配 vless://uuid@ip:port 格式
            match = re.search(r'@([\d\.]+):(\d+)', node)
            if match:
                ip = match.group(1)
                port = match.group(2)
                return f"{ip}:{port}"
        except:
            pass
        return None
    
    def _extract_date_from_node(self, node: str) -> Optional[datetime]:
        """从节点别名中提取日期"""
        try:
            # 从备注中提取日期
            # 格式如: 自选1201-01-443-127.0.0.1
            match = re.search(r'自选(\d{2})(\d{2})', node)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                year = datetime.now().year
                
                # 如果月份大于当前月份，可能是去年的节点
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1
                
                return datetime(year, month, day)
        except:
            pass
        
        # 尝试其他日期格式
        try:
            match = re.search(r'(\d{4})[-_](\d{2})[-_](\d{2})', node)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day)
        except:
            pass
        
        return None