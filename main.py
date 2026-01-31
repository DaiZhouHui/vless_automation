#!/usr/bin/env python3
"""
Vless节点自动化工作流 - 简化版本
"""
import os
import sys
import json
import base64
import requests
import urllib.parse
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv  # 导入 dotenv

# 加载 .env 文件
load_dotenv()

from config import config

class SimpleVlessAutomation:
    """简化版本的Vless自动化工作流（使用requests代替aiohttp）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Vless-Automation/1.0"
        })
        
        # 设置代理
        if config.proxies:
            self.session.proxies.update(config.proxies)
            print(f"✅ 已配置代理: {config.proxies}")
    
    def test_connection(self) -> bool:
        """测试GitHub连接"""
        print("🔗 测试GitHub连接...")
        
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}"
        
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                print("✅ GitHub连接成功!")
                return True
            else:
                print(f"❌ GitHub API返回错误: HTTP {response.status_code}")
                print(f"响应: {response.text[:200]}")
                return False
        except requests.exceptions.Timeout:
            print("❌ 连接超时")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接错误: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 未知错误: {str(e)}")
            return False
    
    def download_file(self, file_path: str) -> str:
        """下载GitHub文件"""
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}?ref={config.GITHUB_BRANCH}"
        
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                if content:
                    # GitHub API返回的content可能包含换行符
                    content = content.replace("\n", "")
                    return base64.b64decode(content).decode('utf-8')
                else:
                    return ""
            elif response.status_code == 404:
                print(f"📭 文件不存在: {file_path}")
                return ""
            else:
                print(f"⚠️ 下载文件失败 (HTTP {response.status_code}): {file_path}")
                return ""
        except Exception as e:
            print(f"⚠️ 下载文件异常: {e}")
            return ""
    
    def upload_file(self, file_path: str, content: str, message: str) -> bool:
        """上传文件到GitHub"""
        # 检查文件是否已存在
        file_sha = self._get_file_sha(file_path)
        
        # 准备上传数据
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        data = {
            "message": message,
            "content": encoded_content,
            "branch": config.GITHUB_BRANCH
        }
        
        if file_sha:
            data["sha"] = file_sha
            print(f"📝 更新现有文件: {file_path}")
        else:
            print(f"📝 创建新文件: {file_path}")
        
        # 上传文件
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}"
        
        try:
            response = self.session.put(url, json=data, timeout=config.REQUEST_TIMEOUT)
            if response.status_code in [200, 201]:
                print(f"✅ 上传成功: {file_path}")
                return True
            else:
                print(f"❌ 上传失败 (HTTP {response.status_code}): {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ 上传异常: {e}")
            return False
    
    def _get_file_sha(self, file_path: str) -> str:
        """获取文件的SHA值"""
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}?ref={config.GITHUB_BRANCH}"
        
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                return data.get("sha", "")
        except Exception:
            pass
        
        return ""
    
    def parse_csv(self, csv_content: str):
        """解析CSV内容"""
        if not csv_content.strip():
            return []
        
        ip_port_pairs = []
        
        # 匹配 IP:端口 格式
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
        matches = re.findall(pattern, csv_content)
        
        for ip, port_str in matches:
            if self._is_valid_ip(ip):
                port = int(port_str)
                if 1 <= port <= 65535:
                    ip_port_pairs.append((ip, port))
        
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
        
        return True
    
    def generate_vless_nodes(self, ip_port_pairs):
        """生成Vless节点"""
        nodes = []
        node_counter = {}
        
        for ip, port in ip_port_pairs:
            # 强制使用443端口
            final_port = 443 if config.FORCE_PORT_443 else port
            
            # 生成节点名称
            today = datetime.now().strftime("%m%d")
            
            # 按IP段分组计数
            ip_prefix = ".".join(ip.split(".")[:2])
            if ip_prefix not in node_counter:
                node_counter[ip_prefix] = 0
            
            node_counter[ip_prefix] += 1
            sequence = str(node_counter[ip_prefix]).zfill(2)
            
            remark = f"{config.REMARKS_PREFIX}{today}-{sequence}-{final_port}-{ip}"
            
            # 生成Vless链接
            params = {
                'encryption': 'none',
                'security': 'tls',
                'sni': config.SNI,
                'fp': config.FINGERPRINT,
                'type': 'ws',
                'host': config.HOST,
                'path': config.CUSTOM_PATH,
                'alpn': 'h2,http/1.1',
                'flow': ''
            }
            
            query_params = '&'.join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
            vless_link = f"vless://{config.UUID}@{ip}:{final_port}?{query_params}#{urllib.parse.quote(remark)}"
            
            nodes.append(vless_link)
        
        return nodes
    
    def create_double_base64(self, plain_text: str) -> str:
        """创建双重Base64编码内容"""
        # 第一层Base64
        first_base64 = base64.b64encode(plain_text.encode('utf-8')).decode('ascii')
        
        # 第二层Base64
        second_base64 = base64.b64encode(first_base64.encode('utf-8')).decode('ascii')
        
        return second_base64
    
    def run(self):
        """运行工作流"""
        print("🚀 开始执行Vless节点自动化工作流")
        print(f"📦 目标仓库: {config.GITHUB_REPO}")
        print(f"📁 CSV文件: {config.CSV_SOURCE_DIR}/{config.CSV_FILENAME}")
        print(f"📤 输出文件: {config.REMOTE_NODE_PATH}")
        print("=" * 50)
        
        try:
            # 1. 测试连接
            if not self.test_connection():
                print("❌ 连接测试失败")
                return False
            
            # 2. 下载CSV文件
            print("\n📥 下载CSV文件...")
            csv_path = f"{config.CSV_SOURCE_DIR}/{config.CSV_FILENAME}"
            csv_content = self.download_file(csv_path)
            
            if not csv_content:
                print("📭 CSV文件为空或不存在，跳过本地节点生成")
                csv_content = ""
            
            # 3. 解析CSV并生成节点
            print("\n⚡ 解析CSV并生成Vless节点...")
            ip_port_pairs = self.parse_csv(csv_content)
            
            if ip_port_pairs:
                local_nodes = self.generate_vless_nodes(ip_port_pairs)
                print(f"✅ 生成 {len(local_nodes)} 个本地Vless节点")
                if local_nodes:
                    print(f"示例: {local_nodes[0][:80]}...")
            else:
                local_nodes = []
                print("📭 未从CSV中解析出有效节点")
            
            # 4. 下载远程节点
            print("\n⬇️ 下载远程节点...")
            remote_content = self.download_file(config.REMOTE_NODE_PATH)
            
            remote_nodes = []
            if remote_content:
                try:
                    # 尝试双重Base64解码
                    try:
                        first_decode = base64.b64decode(remote_content).decode('utf-8')
                        second_decode = base64.b64decode(first_decode).decode('utf-8')
                        remote_nodes = [line.strip() for line in second_decode.split('\n') if line.strip()]
                        print("✅ 使用双重Base64解码")
                    except:
                        # 尝试单层解码
                        try:
                            single_decode = base64.b64decode(remote_content).decode('utf-8')
                            remote_nodes = [line.strip() for line in single_decode.split('\n') if line.strip()]
                            print("✅ 使用单层Base64解码")
                        except:
                            # 直接按行分割
                            remote_nodes = [line.strip() for line in remote_content.split('\n') if line.strip()]
                            print("✅ 使用明文解析")
                    
                    # 过滤有效节点
                    remote_nodes = [node for node in remote_nodes if node.startswith('vless://')]
                except Exception as e:
                    print(f"⚠️ 解析远程节点失败: {e}")
            else:
                print("📭 远程节点文件不存在，将创建新文件")
            
            print(f"📥 获取到 {len(remote_nodes)} 个远程节点")
            
            # 5. 合并节点（简单去重）
            print("\n🔄 合并节点...")
            all_nodes = local_nodes + remote_nodes
            
            # 简单去重：基于IP和端口
            unique_nodes = []
            seen = set()
            
            for node in all_nodes:
                # 提取IP和端口
                match = re.search(r'@([\d\.]+):(\d+)', node)
                if match:
                    key = f"{match.group(1)}:{match.group(2)}"
                    if key not in seen:
                        seen.add(key)
                        unique_nodes.append(node)
                else:
                    # 如果无法提取，直接添加
                    if node not in seen:
                        seen.add(node)
                        unique_nodes.append(node)
            
            print(f"✅ 合并后去重得到 {len(unique_nodes)} 个节点")
            
            # 6. 准备上传内容
            print("\n📦 准备上传内容...")
            
            # Base64订阅 (双重编码)
            plain_text = "\n".join(unique_nodes)
            base64_content = self.create_double_base64(plain_text)
            
            print(f"📊 订阅内容长度: {len(plain_text)} 字符")
            print(f"📊 Base64编码后长度: {len(base64_content)} 字符")
            
            # 7. 上传到GitHub
            print("\n📤 上传到GitHub...")
            
            # 上传Base64订阅
            upload_success = self.upload_file(
                config.REMOTE_NODE_PATH,
                base64_content,
                f"自动更新Vless节点 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {len(unique_nodes)}节点"
            )
            
            if upload_success:
                print(f"✅ 成功上传订阅文件到 {config.REMOTE_NODE_PATH}")
                print("\n🎉 工作流执行完成!")
                return True
            else:
                print(f"❌ 上传订阅文件失败")
                return False
            
        except Exception as e:
            print(f"\n❌ 工作流执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("Vless节点自动化工作流")
    print("=" * 50)
    
    # 显示当前目录
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查是否有 .env 文件
    if not os.path.exists(".env"):
        print("⚠️  未找到 .env 文件")
        print("正在创建 .env 文件模板...")
        
        # 创建 .env 文件模板
        with open(".env", "w", encoding="utf-8") as f:
            f.write("# GitHub配置\n")
            f.write("GITHUB_TOKEN=你的GitHub个人访问令牌\n")
            f.write("GITHUB_REPO=DaiZhouHui/CustomNode\n")
            f.write("GITHUB_BRANCH=main\n")
            f.write("\n# 可选: 代理设置 (如果需要)\n")
            f.write("# HTTP_PROXY=http://127.0.0.1:10809\n")
            f.write("# HTTPS_PROXY=http://127.0.0.1:10809\n")
        
        print("✅ 已创建 .env 文件模板")
        print("📝 请编辑 .env 文件并填入你的GitHub Token")
        print("然后重新运行此程序")
        return
    
    # 检查配置
    if not config.validate():
        print("❌ 配置验证失败")
        return
    
    # 显示配置信息
    print(f"📦 目标仓库: {config.GITHUB_REPO}")
    masked_token = config.GITHUB_TOKEN[:4] + "..." + config.GITHUB_TOKEN[-4:] if len(config.GITHUB_TOKEN) > 8 else "***"
    print(f"🔑 GitHub Token: {masked_token}")
    
    # 运行自动化
    automation = SimpleVlessAutomation()
    success = automation.run()
    
    if success:
        print("\n🎊 自动化工作流执行成功!")
        print("=" * 50)
    else:
        print("\n💥 自动化工作流执行失败!")
        print("=" * 50)

if __name__ == "__main__":
    main()