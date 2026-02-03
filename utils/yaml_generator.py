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
               port = getattr(config, 'DEFAULT_PORT', 443)
        
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
        
        # 处理alpn参数，确保是列表格式
        alpn_param = params.get('alpn', '')
        if alpn_param:
            alpn_list = [a.strip() for a in alpn_param.split(',') if a.strip()]
        else:
            alpn_list = ['h2', 'http/1.1']
        
        # 获取配置中的默认值
        sni = params.get('sni', getattr(config, 'SNI', ''))
        host = params.get('host', getattr(config, 'HOST', ''))
        custom_path = params.get('path', getattr(config, 'CUSTOM_PATH', '/'))
        fingerprint = params.get('fp', getattr(config, 'FINGERPRINT', 'chrome'))
        
        # 构建代理信息
        proxy_info = {
            'name': remark or f"节点-{server}:{port}",
            'type': 'vless',
            'server': server,
            'port': port,
            'uuid': uuid,
            'network': params.get('type', 'ws'),
            'tls': params.get('security') == 'tls',
            'sni': sni,
            'host': host,
            'path': custom_path,
            'alpn': alpn_list,
            'fingerprint': fingerprint,
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
        
        # 清理代理名称中的特殊字符
        safe_proxies = []
        safe_proxy_names = []
        
        for proxy in proxies:
            # 创建副本
            safe_proxy = proxy.copy()
            
            # 清理代理名称
            original_name = safe_proxy['name']
            # 移除不可打印字符
            safe_name = ''.join(c for c in original_name if c.isprintable() or c.isspace())
            safe_name = safe_name.replace('\n', '').replace('\r', '').strip()
            
            if not safe_name:
                safe_name = f"节点-{safe_proxy['server']}:{safe_proxy['port']}"
            
            # 简化名称，移除可能导致问题的字符
            safe_name = re.sub(r'[{}<>\[\]|&*#!%^@`~]', '', safe_name)
            safe_name = safe_name.strip()
            
            safe_proxy['name'] = safe_name
            safe_proxies.append(safe_proxy)
            safe_proxy_names.append(safe_name)
        
        # 代理配置部分 - 使用更安全的生成方式
        proxies_yaml_lines = []
        for proxy in safe_proxies:
            # 构建代理配置行
            proxy_lines = []
            proxy_lines.append(f"  - name: \"{proxy['name']}\"")
            proxy_lines.append(f"    type: {proxy['type']}")
            proxy_lines.append(f"    server: \"{proxy['server']}\"")
            proxy_lines.append(f"    port: {proxy['port']}")
            proxy_lines.append(f"    uuid: \"{proxy['uuid']}\"")
            proxy_lines.append(f"    network: \"{proxy['network']}\"")
            proxy_lines.append(f"    tls: {str(proxy['tls']).lower()}")
            
            if proxy['tls']:
                if proxy['sni']:
                    proxy_lines.append(f"    servername: \"{proxy['sni']}\"")
                if proxy['fingerprint']:
                    proxy_lines.append(f"    fingerprint: \"{proxy['fingerprint']}\"")
                
                # 正确处理alpn为列表格式
                if proxy.get('alpn') and isinstance(proxy['alpn'], list):
                    proxy_lines.append(f"    alpn:")
                    for alpn_item in proxy['alpn']:
                        # 清理alpn项目
                        alpn_item = alpn_item.strip()
                        if alpn_item:
                            proxy_lines.append(f"      - \"{alpn_item}\"")
            
            if proxy['network'] == 'ws':
                proxy_lines.append(f"    ws-opts:")
                proxy_lines.append(f"      path: \"{proxy['path']}\"")
                proxy_lines.append(f"      headers:")
                proxy_lines.append(f"        Host: \"{proxy['host']}\"")
            
            proxy_lines.append(f"    udp: {str(proxy['udp']).lower()}")
            proxy_lines.append(f"    skip-cert-verify: {str(proxy['skip-cert-verify']).lower()}")
            proxy_lines.append("")  # 空行分隔
            
            proxies_yaml_lines.extend(proxy_lines)
        
        proxies_yaml = '\n'.join(proxies_yaml_lines)
        
        # 代理名称列表
        proxy_names_yaml_lines = []
        for name in safe_proxy_names:
            proxy_names_yaml_lines.append(f"      - \"{name}\"")
        proxy_names_yaml = '\n'.join(proxy_names_yaml_lines)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建完整YAML - 使用更简单的模板
        yaml_template = f"""# Clash 配置
# 生成时间: {timestamp}
# 节点数量: {len(safe_proxies)}

mixed-port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info
external-controller: 127.0.0.1:9090

proxies:
{proxies_yaml}

proxy-groups:
  - name: 🚀 节点选择
    type: select
    proxies:
{proxy_names_yaml}
  - name: ♻️ 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    proxies:
{proxy_names_yaml}
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
        
        # 验证YAML格式
        return YamlGenerator._validate_yaml(yaml_template)
    
    @staticmethod
    def _validate_yaml(yaml_content: str) -> str:
        """验证和修复YAML格式"""
        lines = yaml_content.strip().split('\n')
        validated_lines = []
        
        # 修复alpn列表缩进
        in_alpn_list = False
        alpn_indent = 0
        
        for i, line in enumerate(lines, 1):
            line = line.rstrip()
            
            # 跳过空行
            if not line.strip():
                validated_lines.append('')
                in_alpn_list = False
                continue
            
            # 检查是否进入或退出alpn列表
            if 'alpn:' in line and not line.strip().startswith('#'):
                in_alpn_list = True
                alpn_indent = len(line) - len(line.lstrip())
                validated_lines.append(line)
                continue
            elif in_alpn_list and (len(line) - len(line.lstrip())) <= alpn_indent:
                in_alpn_list = False
            
            # 检查行格式
            if ':' in line and not in_alpn_list:
                # 统计前导空格
                leading_spaces = len(line) - len(line.lstrip())
                indent = ' ' * leading_spaces
                
                key_value = line.split(':', 1)
                key = key_value[0].strip()
                value = key_value[1].strip() if len(key_value) > 1 else ""
                
                # 重建行
                if value:
                    # 检查值是否需要引号
                    if any(char in value for char in ':[]{}#&*!|>\\%@`\''):
                        # 转义值中的双引号
                        value = value.replace('"', '\\"')
                        line = f"{indent}{key}: \"{value}\""
                    else:
                        line = f"{indent}{key}: {value}"
                else:
                    line = f"{indent}{key}:"
            
            validated_lines.append(line)
        
        # 确保最后一行不为空
        while validated_lines and not validated_lines[-1].strip():
            validated_lines.pop()
        
        return '\n'.join(validated_lines)
    
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