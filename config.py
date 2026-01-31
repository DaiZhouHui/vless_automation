import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

# 添加这一行导入 dotenv
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

@dataclass
class Config:
    """配置文件"""
    
    # GitHub配置
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "DaiZhouHui/CustomNode")
    GITHUB_BRANCH: str = os.getenv("GITHUB_BRANCH", "main")
    
    # 代理配置
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
    HTTPS_PROXY: str = os.getenv("HTTPS_PROXY", "")
    
    # 文件路径配置
    CSV_SOURCE_DIR: str = "f_node"
    CSV_FILENAME: str = "results.csv"
    REMOTE_NODE_PATH: str = "AutoNode"  # 远程订阅路径
    YAML_FILE_NAME: str = "AutoNode.yaml"  # YAML配置文件
    
    # Vless配置
    UUID: str = "471a8e64-7b21-4703-b1d1-45a221098459"
    HOST: str = "knny.dpdns.org"
    SNI: str = "knny.dpdns.org"
    FINGERPRINT: str = "chrome"
    DEFAULT_PORT: int = 443
    FORCE_PORT_443: bool = True
    REMARKS_PREFIX: str = "自选"
    CUSTOM_PATH: str = "/?ed=2048"
    
    # 网络配置
    REQUEST_TIMEOUT: int = 30  # 请求超时时间(秒)
    MAX_RETRIES: int = 3  # 最大重试次数
    
    # 节点管理配置
    MAX_DAYS_TO_KEEP: int = 10  # 保留最近10天的节点
    AUTO_DELETE_OLD_NODES: bool = True
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/vless_automation.log"
    
    # 运行配置
    CHECK_INTERVAL_HOURS: int = 24  # 每天运行一次
    
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量创建配置"""
        return cls(
            GITHUB_TOKEN=os.getenv("GITHUB_TOKEN", ""),
            GITHUB_REPO=os.getenv("GITHUB_REPO", "DaiZhouHui/CustomNode"),
            GITHUB_BRANCH=os.getenv("GITHUB_BRANCH", "main"),
            HTTP_PROXY=os.getenv("HTTP_PROXY", ""),
            HTTPS_PROXY=os.getenv("HTTPS_PROXY", "")
        )
    
    def validate(self) -> bool:
        """验证配置"""
        if not self.GITHUB_TOKEN:
            print("❌ 错误: 缺少GITHUB_TOKEN环境变量")
            print("请在当前目录下创建 .env 文件并设置GITHUB_TOKEN")
            print("或设置系统环境变量")
            print("\n.env 文件示例:")
            print("""
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=DaiZhouHui/CustomNode
GITHUB_BRANCH=main
            """)
            return False
        if not self.GITHUB_REPO or "/" not in self.GITHUB_REPO:
            print("❌ 错误: GITHUB_REPO格式不正确 (应为: 用户名/仓库名)")
            return False
        
        # 检查代理设置
        if self.HTTP_PROXY or self.HTTPS_PROXY:
            print(f"🔧 使用代理: HTTP={self.HTTP_PROXY}, HTTPS={self.HTTPS_PROXY}")
        
        return True
    
    @property
    def proxies(self):
        """获取代理配置"""
        proxies = {}
        if self.HTTP_PROXY:
            proxies['http'] = self.HTTP_PROXY
        if self.HTTPS_PROXY:
            proxies['https'] = self.HTTPS_PROXY
        return proxies if proxies else None

# 创建配置实例
config = Config.from_env()