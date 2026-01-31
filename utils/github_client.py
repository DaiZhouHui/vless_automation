"""
GitHub API客户端
"""
import base64
import json
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
import time
from config import config

class GitHubClient:
    """GitHub API客户端"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Vless-Automation/1.0"
        }
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        
    async def test_connection(self) -> bool:
        """测试GitHub连接"""
        print("🔗 测试GitHub连接...")
        
        for retry in range(self.config.MAX_RETRIES):
            try:
                url = f"{self.base_url}/repos/{self.config.GITHUB_REPO}"
                
                # 创建连接器
                connector = aiohttp.TCPConnector(limit=10)
                
                # 准备代理
                proxy = self.config.HTTPS_PROXY or self.config.HTTP_PROXY
                
                async with aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=self.timeout,
                    connector=connector
                ) as session:
                    
                    async with session.get(url, proxy=proxy) as response:
                        if response.status == 200:
                            print(f"✅ GitHub连接成功 (尝试 {retry + 1}/{self.config.MAX_RETRIES})")
                            return True
                        else:
                            print(f"❌ GitHub API返回错误: HTTP {response.status}")
                            if retry < self.config.MAX_RETRIES - 1:
                                await asyncio.sleep(2 ** retry)  # 指数退避
                
            except aiohttp.ClientConnectorError as e:
                print(f"❌ 连接错误 (尝试 {retry + 1}/{self.config.MAX_RETRIES}): {str(e)}")
                if retry < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** retry)
            except asyncio.TimeoutError:
                print(f"❌ 连接超时 (尝试 {retry + 1}/{self.config.MAX_RETRIES})")
                if retry < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** retry)
            except Exception as e:
                print(f"❌ 未知错误 (尝试 {retry + 1}/{self.config.MAX_RETRIES}): {str(e)}")
                if retry < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** retry)
        
        print("❌ GitHub连接测试失败，达到最大重试次数")
        return False
    
    async def download_file(self, file_path: str) -> Optional[str]:
        """
        下载GitHub文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 文件内容
        """
        for retry in range(self.config.MAX_RETRIES):
            try:
                url = f"{self.base_url}/repos/{self.config.GITHUB_REPO}/contents/{file_path}?ref={self.config.GITHUB_BRANCH}"
                proxy = self.config.HTTPS_PROXY or self.config.HTTP_PROXY
                
                async with aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=self.timeout
                ) as session:
                    
                    async with session.get(url, proxy=proxy) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data.get("content", "")
                            
                            # Base64解码
                            if content:
                                # GitHub API返回的content可能包含换行符
                                content = content.replace("\n", "")
                                return base64.b64decode(content).decode('utf-8')
                        elif response.status == 404:
                            print(f"📭 文件不存在: {file_path}")
                            return None
                        else:
                            print(f"⚠️ 下载文件失败 (HTTP {response.status}): {file_path}")
                            if retry < self.config.MAX_RETRIES - 1:
                                await asyncio.sleep(2 ** retry)
                                continue
                
            except Exception as e:
                print(f"⚠️ 下载文件异常 (尝试 {retry + 1}): {e}")
                if retry < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** retry)
        
        return None
    
    async def download_remote_nodes(self, node_path: str) -> List[str]:
        """
        下载远程节点
        
        Args:
            node_path: 节点文件路径
            
        Returns:
            List[str]: 远程节点列表
        """
        content = await self.download_file(node_path)
        
        if not content:
            return []
        
        try:
            # 尝试双重Base64解码
            try:
                # 第一层解码
                first_decode = base64.b64decode(content).decode('utf-8')
                # 第二层解码
                second_decode = base64.b64decode(first_decode).decode('utf-8')
                nodes = [line.strip() for line in second_decode.split('\n') if line.strip()]
            except:
                # 如果双重解码失败，尝试单层解码
                try:
                    single_decode = base64.b64decode(content).decode('utf-8')
                    nodes = [line.strip() for line in single_decode.split('\n') if line.strip()]
                except:
                    # 如果都不是，直接按行分割
                    nodes = [line.strip() for line in content.split('\n') if line.strip() and line.startswith('vless://')]
            
            # 过滤有效节点
            valid_nodes = []
            for node in nodes:
                if node.startswith('vless://'):
                    valid_nodes.append(node)
            
            return valid_nodes
            
        except Exception as e:
            print(f"⚠️ 解析远程节点失败: {e}")
            return []
    
    async def upload_file(self, file_path: str, content: str, 
                         message: str, is_base64: bool = True) -> bool:
        """
        上传文件到GitHub
        
        Args:
            file_path: 文件路径
            content: 文件内容
            message: 提交信息
            is_base64: 内容是否为Base64编码
            
        Returns:
            bool: 是否成功
        """
        for retry in range(self.config.MAX_RETRIES):
            try:
                # 1. 检查文件是否已存在
                file_sha = await self._get_file_sha(file_path)
                
                # 2. 准备上传数据
                if is_base64:
                    # 内容已经是Base64
                    encoded_content = content
                else:
                    # 文本内容需要Base64编码
                    encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
                
                data = {
                    "message": message,
                    "content": encoded_content,
                    "branch": self.config.GITHUB_BRANCH
                }
                
                if file_sha:
                    data["sha"] = file_sha
                
                # 3. 上传文件
                url = f"{self.base_url}/repos/{self.config.GITHUB_REPO}/contents/{file_path}"
                proxy = self.config.HTTPS_PROXY or self.config.HTTP_PROXY
                
                async with aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=self.timeout
                ) as session:
                    
                    async with session.put(url, json=data, proxy=proxy) as response:
                        if response.status in [200, 201]:
                            print(f"✅ 上传成功: {file_path}")
                            return True
                        else:
                            error_data = await response.text()
                            print(f"❌ 上传失败 (HTTP {response.status}): {error_data[:200]}")
                            if retry < self.config.MAX_RETRIES - 1:
                                await asyncio.sleep(2 ** retry)
                                continue
                
            except Exception as e:
                print(f"❌ 上传异常 (尝试 {retry + 1}): {e}")
                if retry < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** retry)
        
        return False
    
    async def _get_file_sha(self, file_path: str) -> Optional[str]:
        """获取文件的SHA值"""
        try:
            url = f"{self.base_url}/repos/{self.config.GITHUB_REPO}/contents/{file_path}?ref={self.config.GITHUB_BRANCH}"
            proxy = self.config.HTTPS_PROXY or self.config.HTTP_PROXY
            
            async with aiohttp.ClientSession(
                headers=self.headers,
                timeout=self.timeout
            ) as session:
                
                async with session.get(url, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("sha")
                    else:
                        return None
        except Exception:
            return None