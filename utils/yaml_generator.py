#!/usr/bin/env python3
"""
YAML配置文件生成器
"""
import re
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

class YamlGenerator:
    """YAML配置文件生成器"""
    
    @staticmethod
    def generate_clash_yaml(nodes: List[str], config) -> str:
        """
        生成Clash YAML配置
        
        Args:
            nodes: Vless节点列表
            config: 配置对象
            
        Returns:
            str: YAML配置内容
        """
        if not nodes:
            print("⚠️ 没有节点数据，生成空的YAML配置")
            return YamlGenerator._generate_empty_yaml()
        
        # 解析节点
        proxies = []
        proxy_names = []
        
        for i, node in enumerate(nodes):
            try:
                proxy_info = YamlGenerator._parse_vless_url(node, config)
                if proxy_info:
                    proxy_name = proxy_info['name']
                    proxy_names.append(proxy_name)
                    proxies.append(proxy_info)
            except Exception as e:
                print(f"⚠️ 解析节点失败 ({i+1}/{len(nodes)}): {e}")
                continue
        
        print(f"✅ 成功解析 {len(proxies)} 个节点用于YAML配置")
        
        # 生成YAML内容
        yaml_content = YamlGenerator._build_yaml_content(proxies, proxy_names, config)
        
        return yaml_content
    
    @staticmethod
    def _parse_vless_url(url: str, config) -> Dict[str, Any]:
        """解析Vless URL"""
        if not url.startswith("vless://"):
            raise ValueError("不是有效的Vless链接")
        
        # 移除协议头
        url = url[8:]
        
        # 分割UUID和服务器部分
        if "@" not in url:
            raise ValueError("无效的Vless格式")
        
        uuid, rest = url.split("@", 1)
        
        # 分割服务器和查询参数
        if "?" in rest:
            server_port, query_part = rest.split("?", 1)
        else:
            server_port = rest
            query_part = ""
        
        # 分割服务器和端口
        if ":" not in server_port:
            raise ValueError("缺少端口号")
        
        server, port_str = server_port.rsplit(":", 1)
        try:
            port = int(port_str)
        except:
            port = config.DEFAULT_PORT
        
        # 提取备注
        remark = ""
        if "#" in query_part:
            query_part, remark = query_part.split("#", 1)
            remark = urllib.parse.unquote(remark)
        
        # 解析查询参数
        params = {}
        if query_part:
            for param in query_part.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key] = urllib.parse.unquote(value)
        
        # 构建代理信息
        proxy_info = {
            'name': remark or f"节点-{server}:{port}",
            'type': 'vless',
            'server': server,
            'port': port,
            'uuid': uuid,
            'network': params.get('type', 'ws'),
            'tls': params.get('security') == 'tls',
            'sni': params.get('sni', config.SNI),
            'host': params.get('host', config.HOST),
            'path': params.get('path', config.CUSTOM_PATH),
            'alpn': params.get('alpn', 'h2,http/1.1').split(','),
            'fingerprint': params.get('fp', config.FINGERPRINT),
            'udp': True,
            'skip-cert-verify': False
        }
        
        return proxy_info
    
    @staticmethod
    def _build_yaml_content(proxies: List[Dict], proxy_names: List[str], config) -> str:
        """构建YAML内容"""
        
        # 如果没有代理，生成最小的有效配置
        if not proxies:
            return """mixed-port: 7890
allow-lan: true
mode: rule
log-level: info
proxies: []
proxy-groups:
  - name: 🚀 代理
    type: select
    proxies: []
rules:
  - GEOIP,CN,DIRECT
  - MATCH,🚀 代理
"""
        
        # 清理代理名称中的特殊字符，确保YAML安全
        safe_proxies = []
        safe_proxy_names = []
        
        for proxy in proxies:
            # 创建副本以避免修改原始数据
            safe_proxy = proxy.copy()
            
            # 清理代理名称中的特殊字符
            original_name = safe_proxy['name']
            safe_name = "".join(c for c in original_name if c.isprintable())
            safe_name = safe_name.replace('\n', '').replace('\r', '').strip()
            if not safe_name:
                safe_name = f"节点-{safe_proxy['server']}:{safe_proxy['port']}"
            
            safe_proxy['name'] = safe_name
            safe_proxies.append(safe_proxy)
            safe_proxy_names.append(safe_name)
        
        # 代理配置部分
        proxies_yaml = ""
        for proxy in safe_proxies:
            proxies_yaml += f"  - name: {proxy['name']}\n"
            proxies_yaml += f"    type: {proxy['type']}\n"
            proxies_yaml += f"    server: {proxy['server']}\n"
            proxies_yaml += f"    port: {proxy['port']}\n"
            proxies_yaml += f"    uuid: {proxy['uuid']}\n"
            proxies_yaml += f"    network: {proxy['network']}\n"
            proxies_yaml += f"    tls: {proxy['tls']}\n"
            
            if proxy['tls']:
                proxies_yaml += f"    servername: {proxy['sni']}\n"
                proxies_yaml += f"    fingerprint: {proxy['fingerprint']}\n"
                proxies_yaml += f"    alpn: {proxy['alpn']}\n"
            
            if proxy['network'] == 'ws':
                proxies_yaml += f"    ws-opts:\n"
                proxies_yaml += f"      path: \"{proxy['path']}\"\n"
                proxies_yaml += f"      headers:\n"
                proxies_yaml += f"        Host: \"{proxy['host']}\"\n"
            
            proxies_yaml += f"    udp: {proxy['udp']}\n"
            proxies_yaml += f"    skip-cert-verify: {proxy['skip-cert-verify']}\n"
            proxies_yaml += "\n"
        
        # 代理名称列表
        proxy_names_yaml = ""
        for name in safe_proxy_names:
            proxy_names_yaml += f"      - {name}\n"
        
        # 完整的YAML模板
        yaml_template = f"""mixed-port: 7890
socks-port: 7891
redir-port: 7892
tproxy-port: 7895
allow-lan: true
bind-address: '*'
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:9090
external-ui: dashboard
secret: ""
dns:
  enable: true
  ipv6: false
  listen: 0.0.0.0:53
  enhanced-mode: redir-host
  nameserver:
    - 8.8.8.8
    - 114.114.114.114
    - 223.5.5.5
  fallback:
    - 1.1.1.1
    - 8.8.4.4
  fallback-filter:
    geoip: true
    geoip-code: CN
    ipcidr:
      - 240.0.0.0/4

proxies:
{proxies_yaml.strip()}

proxy-groups:
  - name: 🚀 节点选择
    type: select
    proxies:
{proxy_names_yaml.strip()}
  - name: ♻️ 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    lazy: true
    proxies:
{proxy_names_yaml.strip()}
  - name: 📲 国外媒体
    type: select
    proxies:
      - 🚀 节点选择
      - ♻️ 自动选择
      - DIRECT

rules:
  - DOMAIN-SUFFIX,openai.com,📲 国外媒体
  - DOMAIN-SUFFIX,chatgpt.com,📲 国外媒体
  - DOMAIN-SUFFIX,bing.com,📲 国外媒体
  - DOMAIN-SUFFIX,github.com,📲 国外媒体
  - DOMAIN-SUFFIX,gitlab.com,📲 国外媒体
  - DOMAIN-SUFFIX,twitter.com,📲 国外媒体
  - DOMAIN-SUFFIX,facebook.com,📲 国外媒体
  - DOMAIN-SUFFIX,instagram.com,📲 国外媒体
  - DOMAIN-SUFFIX,youtube.com,📲 国外媒体
  - DOMAIN-SUFFIX,netflix.com,📲 国外媒体
  - DOMAIN-SUFFIX,disneyplus.com,📲 国外媒体
  - DOMAIN-SUFFIX,spotify.com,📲 国外媒体
  - DOMAIN-SUFFIX,telegram.org,📲 国外媒体
  - DOMAIN-SUFFIX,whatsapp.com,📲 国外媒体
  - DOMAIN-SUFFIX,discord.com,📲 国外媒体
  - DOMAIN-SUFFIX,google.com,📲 国外媒体
  - DOMAIN-SUFFIX,gstatic.com,📲 国外媒体
  - GEOIP,CN,DIRECT
  - MATCH,🚀 节点选择
"""
        
        # 确保YAML是有效的UTF-8
        return yaml_template.encode('utf-8', 'ignore').decode('utf-8')
    
    @staticmethod
    def _generate_empty_yaml() -> str:
        """生成空的YAML配置"""
        return """mixed-port: 7890
allow-lan: true
mode: rule
log-level: info
proxies: []
proxy-groups:
  - name: 🚀 代理
    type: select
    proxies: []
rules:
  - GEOIP,CN,DIRECT
  - MATCH,🚀 代理
"""