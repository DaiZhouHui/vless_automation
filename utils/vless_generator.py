"""
Vless节点生成器
"""
import base64
import urllib.parse
from typing import List, Tuple
from datetime import datetime
from config import config

class VlessGenerator:
    """Vless节点生成器"""
    
    def __init__(self, config):
        self.config = config
        self.node_counter = {}  # 用于序号计数
    
    def generate_from_ip_port(self, ip_port_pairs: List[Tuple[str, int]]) -> List[str]:
        """
        从IP和端口生成Vless节点
        
        Args:
            ip_port_pairs: IP和端口列表
            
        Returns:
            List[str]: Vless节点链接列表
        """
        nodes = []
        
        for ip, port in ip_port_pairs:
            # 强制使用443端口
            final_port = 443 if self.config.FORCE_PORT_443 else port
            
            # 生成节点名称
            remark = self._generate_remark(ip, final_port)
            
            # 生成Vless链接
            vless_link = self._generate_vless_link(ip, final_port, remark)
            nodes.append(vless_link)
        
        # 重置计数器
        self.node_counter.clear()
        
        return nodes
    
    def _generate_remark(self, ip: str, port: int) -> str:
        """生成节点备注名称"""
        # 这里可以根据需要添加地理位置信息
        # 简化版本：使用日期和序号
        today = datetime.now().strftime("%m%d")
        
        # 按IP段分组计数
        ip_prefix = ".".join(ip.split(".")[:2])
        if ip_prefix not in self.node_counter:
            self.node_counter[ip_prefix] = 0
        
        self.node_counter[ip_prefix] += 1
        sequence = str(self.node_counter[ip_prefix]).zfill(2)
        
        return f"{self.config.REMARKS_PREFIX}{today}-{sequence}-{port}-{ip}"
    
    def _generate_vless_link(self, ip: str, port: int, remark: str) -> str:
        """生成Vless链接"""
        params = {
            'encryption': 'none',
            'security': 'tls',
            'sni': self.config.SNI,
            'fp': self.config.FINGERPRINT,
            'type': 'ws',
            'host': self.config.HOST,
            'path': self.config.CUSTOM_PATH,
            'alpn': 'h2,http/1.1',
            'flow': ''
        }
        
        # 构建查询参数
        query_params = '&'.join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
        
        # 构建完整链接
        vless_link = f"vless://{self.config.UUID}@{ip}:{port}?{query_params}#{urllib.parse.quote(remark)}"
        
        return vless_link
    
    def create_double_base64(self, plain_text: str) -> str:
        """
        创建双重Base64编码内容
        
        Args:
            plain_text: 明文节点文本
            
        Returns:
            str: 双重Base64编码内容
        """
        # 第一层Base64
        first_base64 = base64.b64encode(plain_text.encode('utf-8')).decode('ascii')
        
        # 第二层Base64
        second_base64 = base64.b64encode(first_base64.encode('utf-8')).decode('ascii')
        
        return second_base64
    
    def generate_clash_yaml(self, nodes: List[str]) -> str:
        """
        生成Clash YAML配置
        
        Args:
            nodes: Vless节点列表
            
        Returns:
            str: YAML配置内容
        """
        yaml_template = """mixed-port: 7890
allow-lan: true
mode: rule
log-level: info
external-controller: 127.0.0.1:9090
ipv6: false

dns:
  enable: true
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  nameserver:
    - 8.8.8.8
    - 223.5.5.5
    - 1.1.1.1

proxies:
{proxies}

proxy-groups:
  - name: 🚀 节点选择
    type: select
    proxies:
{proxy_names}
  - name: ♻️ 自动选择
    type: url-test
    proxies:
{proxy_names}
    url: http://www.gstatic.com/generate_204
    interval: 300

rules:
  - DOMAIN-SUFFIX,google.com,♻️ 自动选择
  - DOMAIN-SUFFIX,youtube.com,♻️ 自动选择
  - DOMAIN-SUFFIX,github.com,♻️ 自动选择
  - DOMAIN-SUFFIX,twitter.com,♻️ 自动选择
  - DOMAIN-SUFFIX,netflix.com,♻️ 自动选择
  - GEOIP,CN,DIRECT
  - MATCH,♻️ 自动选择
"""
        
        # 解析节点并生成代理配置
        proxies = []
        proxy_names = []
        
        for i, node in enumerate(nodes):
            try:
                # 从Vless链接中提取信息
                uuid, server, port, remark = self._parse_vless_url(node)
                
                proxy_name = remark if remark else f"节点{i+1}"
                proxy_names.append(proxy_name)
                
                proxy = f"""  - name: {proxy_name}
    type: vless
    server: {server}
    port: {port}
    uuid: {uuid}
    network: ws
    tls: true
    sni: {self.config.SNI}
    udp: true
    skip-cert-verify: false
    ws-opts:
      path: "{self.config.CUSTOM_PATH}"
      headers:
        Host: "{self.config.HOST}"
"""
                proxies.append(proxy)
            except Exception as e:
                print(f"解析节点失败 {node[:50]}...: {e}")
        
        # 替换模板中的占位符
        yaml_content = yaml_template.format(
            proxies="\n".join(proxies),
            proxy_names="\n".join([f"      - {name}" for name in proxy_names])
        )
        
        return yaml_content
    
    def _parse_vless_url(self, url: str) -> Tuple[str, str, int, str]:
        """解析Vless URL"""
        if not url.startswith("vless://"):
            raise ValueError("不是有效的Vless链接")
        
        # 移除协议头
        url = url[8:]
        
        # 分割UUID和服务器部分
        uuid, rest = url.split("@", 1)
        
        # 分割服务器和查询参数
        if "?" in rest:
            server_port, query = rest.split("?", 1)
        else:
            server_port = rest
            query = ""
        
        # 分割服务器和端口
        server, port_str = server_port.split(":", 1)
        port = int(port_str)
        
        # 提取备注
        remark = ""
        if "#" in query:
            query, remark = query.split("#", 1)
            remark = urllib.parse.unquote(remark)
        
        return uuid, server, port, remark