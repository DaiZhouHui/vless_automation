#!/usr/bin/env python3
"""
测试网络连接和GitHub API访问
"""
import requests
import os
import sys
import json
from datetime import datetime

def test_github_api():
    """测试GitHub API连接"""
    # 从环境变量获取token
    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("GITHUB_REPO", "DaiZhouHui/CustomNode")
    
    if not token:
        print("❌ 未设置GITHUB_TOKEN环境变量")
        print("请设置环境变量: set GITHUB_TOKEN=your_token_here (Windows)")
        print("或创建 .env 文件")
        return False
    
    # 测试GitHub API
    url = f"https://api.github.com/repos/{repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    print(f"🔗 测试连接到: {url}")
    
    try:
        # 设置超时
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ GitHub API 连接成功!")
            data = response.json()
            print(f"📦 仓库: {data.get('full_name')}")
            print(f"📝 描述: {data.get('description', '无')}")
            print(f"⭐ 星标: {data.get('stargazers_count', 0)}")
            return True
        elif response.status_code == 401:
            print("❌ 认证失败: 无效的GitHub Token")
            print("请确保Token有正确的权限 (repo)")
        elif response.status_code == 404:
            print(f"❌ 仓库未找到: {repo}")
            print("请检查仓库名称格式: 用户名/仓库名")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("❌ 连接超时: 无法在10秒内连接到GitHub")
        print("提示: 可能需要配置代理或检查网络")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法建立连接")
        print("提示: 请检查网络连接或防火墙设置")
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
    
    return False

def test_internet_connection():
    """测试互联网连接"""
    test_urls = [
        "https://api.github.com",
        "https://www.google.com",
        "https://www.baidu.com"
    ]
    
    print("\n🌐 测试互联网连接...")
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url} - 可访问 (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"⚠️  {url} - 连接超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - 连接失败")
        except Exception as e:
            print(f"❌ {url} - 错误: {str(e)}")

def check_environment():
    """检查环境变量"""
    print("🔍 检查环境配置...")
    
    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("GITHUB_REPO", "")
    
    if token:
        masked_token = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
        print(f"✅ GITHUB_TOKEN: {masked_token}")
    else:
        print("❌ GITHUB_TOKEN: 未设置")
    
    if repo:
        print(f"✅ GITHUB_REPO: {repo}")
    else:
        print("❌ GITHUB_REPO: 未设置")
    
    # 检查是否有.env文件
    if os.path.exists(".env"):
        print("✅ 找到 .env 文件")
        with open(".env", "r") as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.strip().startswith("#"):
                    print(f"   {line.strip()}")
    else:
        print("⚠️  未找到 .env 文件")
    
    return bool(token and repo)

def main():
    print("🚀 Vless自动化脚本 - 网络连接测试")
    print("=" * 50)
    
    # 检查环境
    env_ok = check_environment()
    
    if not env_ok:
        print("\n📝 请创建 .env 文件或设置环境变量:")
        print("""
GITHUB_TOKEN=你的GitHub个人访问令牌
GITHUB_REPO=DaiZhouHui/CustomNode
GITHUB_BRANCH=main

# 可选: 代理设置 (如果需要)
# HTTP_PROXY=http://127.0.0.1:10809
# HTTPS_PROXY=http://127.0.0.1:10809
        """)
        
        # 创建.env文件模板
        create_env = input("\n是否创建 .env 文件模板? (y/n): ").lower()
        if create_env == 'y':
            with open(".env", "w") as f:
                f.write("# GitHub配置\n")
                f.write("GITHUB_TOKEN=你的GitHub个人访问令牌\n")
                f.write("GITHUB_REPO=DaiZhouHui/CustomNode\n")
                f.write("GITHUB_BRANCH=main\n")
                f.write("\n# 可选: 代理设置 (如果需要)\n")
                f.write("# HTTP_PROXY=http://127.0.0.1:10809\n")
                f.write("# HTTPS_PROXY=http://127.0.0.1:10809\n")
            print("✅ 已创建 .env 文件模板，请编辑它并填入实际值")
    
    # 测试互联网连接
    test_internet_connection()
    
    # 测试GitHub API
    print("\n" + "=" * 50)
    github_ok = test_github_api()
    
    if github_ok:
        print("\n🎉 所有测试通过! 可以运行 main.py")
        return True
    else:
        print("\n💡 建议:")
        print("1. 检查网络连接")
        print("2. 确保GitHub Token有 repo 权限")
        print("3. 如果需要代理，请配置HTTP_PROXY环境变量")
        print("4. 尝试使用VPN")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)