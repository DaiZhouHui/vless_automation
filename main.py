#!/usr/bin/env python3
"""
Vless节点自动化工作流 - 完整版本
支持本地运行和GitHub Actions
"""
import os
import sys
import json
import base64
import requests
import urllib.parse
import re
from datetime import datetime
from typing import List, Tuple, Optional
from typing import Optional, Dict


# 导入自定义模块
from config import config
from utils.csv_processor import CSVProcessor
from utils.yaml_generator import YamlGenerator

class VlessAutomation:
    """Vless节点自动化工作流"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Vless-Automation/1.0"
        })
        
        # 设置超时
        self.timeout = config.REQUEST_TIMEOUT
        
        # 设置代理
        if config.proxies:
            self.session.proxies.update(config.proxies)
            print(f"🔧 已配置代理: {config.proxies}")
        
        # 检查是否在GitHub Actions中运行
        self.is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
        
        print(f"🔧 运行环境: {'GitHub Actions' if self.is_github_actions else '本地'}")
    
    def test_connection(self) -> bool:
        """测试GitHub连接"""
        print("🔗 测试GitHub连接...")
        
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                repo_info = response.json()
                print(f"✅ GitHub连接成功!")
                print(f"📦 仓库: {repo_info.get('full_name')}")
                print(f"📝 描述: {repo_info.get('description', '无')}")
                print(f"⭐ 星标: {repo_info.get('stargazers_count', 0)}")
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
    
    def download_file(self, file_path: str) -> Optional[str]:
        """
        下载GitHub文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 文件内容
        """
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}?ref={config.GITHUB_BRANCH}"
        
        print(f"📥 下载文件: {file_path}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查文件大小
                size = data.get("size", 0)
                print(f"📊 文件大小: {size} 字节")
                
                content = data.get("content", "")
                if content:
                    # GitHub API返回的content是Base64编码的
                    content = content.replace("\n", "")
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    print(f"✅ 下载成功: {len(decoded_content)} 字符")
                    return decoded_content
                else:
                    print("⚠️ 文件内容为空")
                    return ""
                    
            elif response.status_code == 404:
                print(f"📭 文件不存在: {file_path}")
                return None
            else:
                print(f"❌ 下载失败 (HTTP {response.status_code}): {file_path}")
                return None
                
        except Exception as e:
            print(f"❌ 下载异常: {e}")
            return None
            
    def upload_file(self, file_path: str, content: str, message: str) -> bool:
        """
        上传文件到GitHub
        
        Args:
            file_path: 文件路径
            content: 文件内容
            message: 提交信息
            
        Returns:
            bool: 是否成功
        """
        print(f"\n📤 准备上传文件: {file_path}")
        print(f"提交信息: {message}")
        print(f"内容大小: {len(content)} 字符")
        
        # 检查文件是否已存在
        file_info = self._get_file_info(file_path)
        
        # 检查内容是否为空
        if not content or len(content.strip()) == 0:
            print(f"⚠️ 警告: {file_path} 内容为空!")
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                content = """proxies: []
proxy-groups:
  - name: 🚀 代理
    type: select
    proxies: []
rules:
  - MATCH,🚀 代理"""
        
        # Base64编码内容
        try:
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
            print(f"Base64编码后大小: {len(encoded_content)} 字符")
        except Exception as e:
            print(f"❌ Base64编码失败: {e}")
            return False
        
        # 检查内容是否发生变化
        if file_info and file_info['content'] == encoded_content:
            print(f"✅ 内容未变化，跳过上传: {file_path}")
            print(f"📊 文件SHA: {file_info['sha'][:8]}... (未变化)")
            return True
        
        data = {
            "message": message,
            "content": encoded_content,
            "branch": config.GITHUB_BRANCH
        }
        
        if file_info:
            data["sha"] = file_info['sha']
            print(f"📝 更新现有文件: {file_path}")
        else:
            print(f"📝 创建新文件: {file_path}")
        
        # 上传文件
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}"
        
        print(f"📡 请求URL: {url}")
        
        try:
            response = self.session.put(url, json=data, timeout=self.timeout)
            
            print(f"📡 响应状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"✅ 上传成功: {file_path}")
                response_data = response.json()
                if "content" in response_data:
                    new_sha = response_data.get('content', {}).get('sha', 'N/A')
                    print(f"📄 新文件SHA: {new_sha[:8]}...")
                return True
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    error_data = {"message": response.text[:500]}
                
                print(f"❌ 上传失败 (HTTP {response.status_code}): {file_path}")
                if "message" in error_data:
                    print(f"错误信息: {error_data['message']}")
                
                # 如果是YAML文件，尝试诊断
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    print(f"\n🔍 YAML文件上传失败诊断:")
                    print(f"1. 内容长度: {len(content)}")
                    print(f"2. 内容前200字符: {content[:200]}")
                    print(f"3. 内容是否包含特殊字符: {'是' if any(ord(c) > 127 for c in content[:500]) else '否'}")
                
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ 上传超时: {file_path}")
            return False
        except Exception as e:
            print(f"❌ 上传异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_file_info(self, file_path: str) -> Optional[Dict[str, str]]:
        """获取文件的SHA和内容"""
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}?ref={config.GITHUB_BRANCH}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return {
                    'sha': data.get("sha", ""),
                    'content': data.get("content", "").replace("\n", "")
                }
            else:
                return None
        except Exception as e:
            print(f"⚠️ 获取文件信息失败: {e}")
            return None   



    def _get_file_sha(self, file_path: str) -> Optional[str]:
        """获取文件的SHA值"""
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}?ref={config.GITHUB_BRANCH}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return data.get("sha", "")
        except Exception:
            pass
        
        return None
    
    def generate_vless_nodes(self, ip_port_pairs: List[Tuple[str, int]]) -> List[str]:
        """从IP和端口生成Vless节点"""
        nodes = []
        node_counter = {}
        
        print(f"🔧 生成Vless节点...")
        
        for ip, port in ip_port_pairs:
            # 强制使用443端口（如果配置）
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
            vless_link = self._create_vless_link(ip, final_port, remark)
            nodes.append(vless_link)
        
        print(f"✅ 生成 {len(nodes)} 个Vless节点")
        if nodes:
            print(f"📋 示例节点: {nodes[0][:100]}...")
        
        return nodes
    
    def _create_vless_link(self, ip: str, port: int, remark: str) -> str:
        """创建Vless链接"""
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
        
        # 构建查询参数
        query_params = '&'.join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
        
        # 构建完整链接
        vless_link = f"vless://{config.UUID}@{ip}:{port}?{query_params}#{urllib.parse.quote(remark)}"
        
        return vless_link

    def create_base64(self, plain_text: str) -> str:
        """创建Base64编码内容（单层）"""
        # 只进行一次Base64编码
        encoded_content = base64.b64encode(plain_text.encode('utf-8')).decode('ascii')
        return encoded_content    
    
    def merge_nodes(self, local_nodes: List[str], remote_nodes: List[str]) -> List[str]:
        """合并本地和远程节点，并去重"""
        all_nodes = local_nodes + remote_nodes
        
        # 基于IP和端口去重
        unique_nodes = []
        seen = set()
        
        for node in all_nodes:
            # 提取IP和端口作为唯一标识
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
        
        print(f"📊 节点统计:")
        print(f"  - 本地节点: {len(local_nodes)}")
        print(f"  - 远程节点: {len(remote_nodes)}")
        print(f"  - 去重后节点: {len(unique_nodes)}")
        
        return unique_nodes
    
    def run(self) -> bool:
        """运行工作流"""
        print("=" * 60)
        print("🚀 Vless节点自动化工作流")
        print("=" * 60)
        
        try:
            # 1. 测试连接
            if not self.test_connection():
                return False
            
            print("\n" + "-" * 60)
            
            # 2. 下载CSV文件
            csv_path = f"{config.CSV_SOURCE_DIR}/{config.CSV_FILENAME}"
            csv_content = self.download_file(csv_path)
            
            if csv_content is None:
                print("❌ CSV文件下载失败，终止流程")
                return False
            
            # 3. 解析CSV并生成节点
            if csv_content:
                ip_port_pairs = CSVProcessor.parse_csv(csv_content)
                local_nodes = self.generate_vless_nodes(ip_port_pairs)
            else:
                print("📭 CSV文件内容为空")
                local_nodes = []
            
            # 4. 下载远程节点
            remote_content = self.download_file(config.OUTPUT_NODE_FILE)
            
            remote_nodes = []
            if remote_content:
                try:
                    # 尝试双重Base64解码
                    try:
                        first_decode = base64.b64decode(remote_content).decode('utf-8')
                        second_decode = base64.b64decode(first_decode).decode('utf-8')
                        remote_nodes = [line.strip() for line in second_decode.split('\n') if line.strip()]
                        print("✅ 远程节点使用双重Base64解码")
                    except:
                        # 尝试单层解码
                        try:
                            single_decode = base64.b64decode(remote_content).decode('utf-8')
                            remote_nodes = [line.strip() for line in single_decode.split('\n') if line.strip()]
                            print("✅ 远程节点使用单层Base64解码")
                        except:
                            # 直接按行分割
                            remote_nodes = [line.strip() for line in remote_content.split('\n') if line.strip()]
                            print("✅ 远程节点使用明文解析")
                    
                    # 过滤有效节点
                    remote_nodes = [node for node in remote_nodes if node.startswith('vless://')]
                except Exception as e:
                    print(f"⚠️ 解析远程节点失败: {e}")
            else:
                print("📭 远程节点文件不存在，将创建新文件")
            
            # 5. 合并节点
            unique_nodes = self.merge_nodes(local_nodes, remote_nodes)
            
            if not unique_nodes:
                print("⚠️ 警告: 没有有效的节点数据")
                print("将创建空的订阅文件")
            
            # 6. 准备上传内容
            print("\n📦 准备上传内容...")
             
            # 检查是否需要上传文件
            # Base64订阅 (单层编码)
            plain_text = "\n".join(unique_nodes)
            base64_content = self.create_base64(plain_text)
            
            # 检查AutoNode文件是否需要更新
            auto_node_info = self._get_file_info(config.OUTPUT_NODE_FILE)
            yaml_info = self._get_file_info(config.OUTPUT_YAML_FILE)
            
            # 生成YAML配置
            yaml_content = YamlGenerator.generate_clash_yaml(unique_nodes, config)
            
            print(f"📊 内容统计:")
            print(f"  - 明文节点: {len(plain_text)} 字符")
            print(f"  - Base64订阅: {len(base64_content)} 字符")
            print(f"  - YAML配置: {len(yaml_content)} 字符")
            
            if auto_node_info:
                print(f"  - AutoNode当前SHA: {auto_node_info['sha'][:8]}...")
            if yaml_info:
                print(f"  - YAML当前SHA: {yaml_info['sha'][:8]}...")
            
            # 7. 上传文件到GitHub
            print("\n📤 上传文件到GitHub...")
            
            # 上传Base64订阅文件
            upload_success = self.upload_file(
                config.OUTPUT_NODE_FILE,
                base64_content,
                f"自动更新Vless节点 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {len(unique_nodes)}节点"
            )
            
            if not upload_success:
                print("❌ 上传订阅文件失败")
                return False
            
            # 上传YAML配置文件
            yaml_success = self.upload_file(
                config.OUTPUT_YAML_FILE,
                yaml_content,
                f"更新Clash配置 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {len(unique_nodes)}节点"
            )
            
            if not yaml_success:
                print("❌ 上传YAML配置文件失败")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 工作流执行完成!")
            print(f"✅ 成功上传文件:")
            print(f"  - {config.OUTPUT_NODE_FILE}")
            print(f"  - {config.OUTPUT_YAML_FILE}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ 工作流执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    # 检查配置
    if not config.validate():
        sys.exit(1)
    
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    
    # 运行自动化
    automation = VlessAutomation()
    success = automation.run()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()