#!/usr/bin/env python3
"""
配置文件 - 支持本地和GitHub Actions环境
"""
import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件（仅本地运行）
load_dotenv()

class Config:
    """配置类 - 支持环境变量和默认值"""
    
    def __init__(self):
        # GitHub配置
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", os.getenv("GH_TOKEN", ""))
        self.GITHUB_REPO = os.getenv("GITHUB_REPO", "DaiZhouHui/CustomNode")
        self.GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
        
        # 在GitHub Actions中，可以使用GITHUB_TOKEN
        if not self.GITHUB_TOKEN and os.getenv("GITHUB_ACTIONS") == "true":
            self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
        
        # CSV配置
        self.CSV_SOURCE_DIR = os.getenv("CSV_SOURCE_DIR", "f_node")
        self.CSV_FILENAME = os.getenv("CSV_FILENAME", "results.csv")
        
        # 输出配置
        self.OUTPUT_NODE_FILE = os.getenv("OUTPUT_NODE_FILE", "AutoNode")
        self.OUTPUT_YAML_FILE = os.getenv("OUTPUT_YAML_FILE", "AutoNode.yaml")
        
        # Vless配置
        self.UUID = os.getenv("UUID", "471a8e64-7b21-4703-b1d1-45a221098459")
        self.HOST = os.getenv("HOST", "knny.dpdns.org")
        self.SNI = os.getenv("SNI", "knny.dpdns.org")
        self.FINGERPRINT = os.getenv("FINGERPRINT", "chrome")
        self.DEFAULT_PORT = int(os.getenv("DEFAULT_PORT", "443"))
        self.FORCE_PORT_443 = os.getenv("FORCE_PORT_443", "true").lower() == "true"
        self.REMARKS_PREFIX = os.getenv("REMARKS_PREFIX", "香港节点-")
        self.CUSTOM_PATH = os.getenv("CUSTOM_PATH", "/?ed=2048")
        
        # 节点管理配置
        self.MAX_DAYS_TO_KEEP = int(os.getenv("MAX_DAYS_TO_KEEP", "10"))
        self.AUTO_DELETE_OLD_NODES = os.getenv("AUTO_DELETE_OLD_NODES", "true").lower() == "true"
        
        # 网络配置
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        
        # 代理配置
        self.HTTP_PROXY = os.getenv("HTTP_PROXY", "")
        self.HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")
    
    def validate(self):
        """验证配置"""
        errors = []
        
        if not self.GITHUB_TOKEN:
            errors.append("缺少GITHUB_TOKEN环境变量")
        
        if not self.GITHUB_REPO or "/" not in self.GITHUB_REPO:
            errors.append("GITHUB_REPO格式不正确 (应为: 用户名/仓库名)")
        
        if errors:
            print("❌ 配置错误:")
            for error in errors:
                print(f"  - {error}")
            
            print("\n📝 配置方法:")
            print("1. 本地运行: 创建 .env 文件并设置GITHUB_TOKEN")
            print("2. GitHub Actions: 在仓库设置中添加GITHUB_TOKEN密钥")
            print("\n.env 文件示例:")
            print("GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx")
            print("GITHUB_REPO=DaiZhouHui/CustomNode")
            return False
        
        # 显示配置摘要
        print("✅ 配置验证通过")
        print(f"📦 目标仓库: {self.GITHUB_REPO}")
        print(f"📁 CSV文件: {self.CSV_SOURCE_DIR}/{self.CSV_FILENAME}")
        print(f"📤 输出文件: {self.OUTPUT_NODE_FILE}, {self.OUTPUT_YAML_FILE}")
        
        # 检查代理设置
        if self.HTTP_PROXY or self.HTTPS_PROXY:
            print(f"🔧 使用代理: HTTP={self.HTTP_PROXY}, HTTPS={self.HTTPS_PROXY}")
        
        return True
    
    @property
    def proxies(self):
        """获取代理配置字典"""
        proxies = {}
        if self.HTTP_PROXY:
            proxies['http'] = self.HTTP_PROXY
        if self.HTTPS_PROXY:
            proxies['https'] = self.HTTPS_PROXY
        return proxies if proxies else None

# 创建配置实例
config = Config()