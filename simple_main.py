#!/usr/bin/env python3
"""
最简单的Vless自动化脚本 - 无环境变量依赖
"""
import os
import sys
import base64
import requests
import urllib.parse
import re
from datetime import datetime, timedelta

# 直接在代码中配置
CONFIG = {
    "GITHUB_TOKEN": "你的GitHubToken在这里",  # 请替换为你的实际Token
    "GITHUB_REPO": "DaiZhouHui/CustomNode",
    "GITHUB_BRANCH": "main",
    "CSV_SOURCE_DIR": "f_node",
    "CSV_FILENAME": "results.csv",
    "REMOTE_NODE_PATH": "AutoNode",
    "UUID": "471a8e64-7b21-4703-b1d1-45a221098459",
    "HOST": "knny.dpdns.org",
    "SNI": "knny.dpdns.org",
    "FINGERPRINT": "chrome",
    "DEFAULT_PORT": 443,
    "FORCE_PORT_443": True,
    "REMARKS_PREFIX": "自选",
    "CUSTOM_PATH": "/?ed=2048",
    "MAX_DAYS_TO_KEEP": 10
}

def main():
    print("🚀 最简单的Vless自动化脚本")
    print("=" * 50)
    
    # 检查Token
    if CONFIG["GITHUB_TOKEN"] == "你的GitHubToken在这里":
        print("❌ 请先修改simple_main.py中的GITHUB_TOKEN")
        print("   将 '你的GitHubToken在这里' 替换为您的实际GitHub Token")
        return
    
    # 初始化会话
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {CONFIG['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Vless-Automation/1.0"
    })
    
    print("✅ 配置加载完成")
    print(f"📦 目标仓库: {CONFIG['GITHUB_REPO']}")
    
    # 运行工作流
    try:
        # 1. 下载CSV
        csv_path = f"{CONFIG['CSV_SOURCE_DIR']}/{CONFIG['CSV_FILENAME']}"
        url = f"https://api.github.com/repos/{CONFIG['GITHUB_REPO']}/contents/{csv_path}?ref={CONFIG['GITHUB_BRANCH']}"
        
        print(f"📥 下载CSV文件: {csv_path}")
        response = session.get(url, timeout=30)
        
        csv_content = ""
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "").replace("\n", "")
            csv_content = base64.b64decode(content).decode('utf-8')
            print(f"✅ CSV文件下载成功 ({len(csv_content)} 字符)")
        else:
            print(f"📭 CSV文件不存在或下载失败: HTTP {response.status_code}")
        
        # 2. 解析CSV
        ip_port_pairs = []
        if csv_content:
            pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
            matches = re.findall(pattern, csv_content)
            
            for ip, port_str in matches:
                parts = ip.split('.')
                if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
                    port = int(port_str)
                    if 1 <= port <= 65535:
                        ip_port_pairs.append((ip, port))
        
        print(f"🔍 从CSV解析出 {len(ip_port_pairs)} 个IP:端口对")
        
        # 3. 生成Vless节点
        nodes = []
        node_counter = {}
        
        for ip, port in ip_port_pairs:
            final_port = 443 if CONFIG["FORCE_PORT_443"] else port
            today = datetime.now().strftime("%m%d")
            
            ip_prefix = ".".join(ip.split(".")[:2])
            if ip_prefix not in node_counter:
                node_counter[ip_prefix] = 0
            
            node_counter[ip_prefix] += 1
            sequence = str(node_counter[ip_prefix]).zfill(2)
            remark = f"{CONFIG['REMARKS_PREFIX']}{today}-{sequence}-{final_port}-{ip}"
            
            params = {
                'encryption': 'none',
                'security': 'tls',
                'sni': CONFIG['SNI'],
                'fp': CONFIG['FINGERPRINT'],
                'type': 'ws',
                'host': CONFIG['HOST'],
                'path': CONFIG['CUSTOM_PATH'],
                'alpn': 'h2,http/1.1',
                'flow': ''
            }
            
            query_params = '&'.join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
            vless_link = f"vless://{CONFIG['UUID']}@{ip}:{final_port}?{query_params}#{urllib.parse.quote(remark)}"
            nodes.append(vless_link)
        
        print(f"⚡ 生成 {len(nodes)} 个Vless节点")
        
        # 4. 下载远程节点
        remote_nodes = []
        remote_url = f"https://api.github.com/repos/{CONFIG['GITHUB_REPO']}/contents/{CONFIG['REMOTE_NODE_PATH']}?ref={CONFIG['GITHUB_BRANCH']}"
        
        response = session.get(remote_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            remote_content = data.get("content", "").replace("\n", "")
            decoded = base64.b64decode(remote_content).decode('utf-8')
            
            # 尝试双重解码
            try:
                decoded2 = base64.b64decode(decoded).decode('utf-8')
                remote_nodes = [line.strip() for line in decoded2.split('\n') if line.strip()]
            except:
                remote_nodes = [line.strip() for line in decoded.split('\n') if line.strip()]
            
            remote_nodes = [node for node in remote_nodes if node.startswith('vless://')]
        
        print(f"📥 下载 {len(remote_nodes)} 个远程节点")
        
        # 5. 合并去重
        all_nodes = nodes + remote_nodes
        unique_nodes = []
        seen = set()
        
        for node in all_nodes:
            match = re.search(r'@([\d\.]+):(\d+)', node)
            if match:
                key = f"{match.group(1)}:{match.group(2)}"
                if key not in seen:
                    seen.add(key)
                    unique_nodes.append(node)
            elif node not in seen:
                seen.add(node)
                unique_nodes.append(node)
        
        print(f"🔄 合并去重后: {len(unique_nodes)} 个节点")
        
        # 6. 上传到GitHub
        plain_text = "\n".join(unique_nodes)
        first_base64 = base64.b64encode(plain_text.encode('utf-8')).decode('ascii')
        second_base64 = base64.b64encode(first_base64.encode('utf-8')).decode('ascii')
        
        # 获取文件SHA
        file_sha = None
        response = session.get(remote_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            file_sha = data.get("sha", "")
        
        # 上传数据
        upload_data = {
            "message": f"自动更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": second_base64,
            "branch": CONFIG["GITHUB_BRANCH"]
        }
        
        if file_sha:
            upload_data["sha"] = file_sha
        
        response = session.put(remote_url, json=upload_data, timeout=30)
        
        if response.status_code in [200, 201]:
            print(f"✅ 成功上传到 {CONFIG['REMOTE_NODE_PATH']}")
            print(f"🎉 自动化脚本执行完成!")
        else:
            print(f"❌ 上传失败: HTTP {response.status_code}")
            print(f"响应: {response.text[:200]}")
    
    except Exception as e:
        print(f"💥 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()