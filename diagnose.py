#!/usr/bin/env python3
"""
诊断脚本 - 检查所有可能的问题
"""
import os
import sys
import json
import requests

def check_env_file():
    """检查.env文件"""
    print("=" * 60)
    print("1. 检查 .env 文件")
    print("=" * 60)
    
    if os.path.exists(".env"):
        print("✅ 找到 .env 文件")
        
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"文件内容:\n{content}")
            
            # 检查格式
            lines = content.strip().split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" not in line:
                        print(f"❌ 第{i}行格式错误: 缺少等号")
                    else:
                        key, value = line.split("=", 1)
                        if not key.strip():
                            print(f"❌ 第{i}行格式错误: 键名为空")
    else:
        print("❌ 未找到 .env 文件")
        print("请创建 .env 文件并添加以下内容:")
        print("""
GITHUB_TOKEN=你的GitHub令牌
GITHUB_REPO=DaiZhouHui/CustomNode
GITHUB_BRANCH=main
        """)

def check_python_version():
    """检查Python版本"""
    print("\n" + "=" * 60)
    print("2. 检查Python版本")
    print("=" * 60)
    
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
        print("✅ Python版本符合要求 (3.8+)")
    else:
        print("❌ Python版本过低，建议升级到3.8+")

def check_dependencies():
    """检查依赖包"""
    print("\n" + "=" * 60)
    print("3. 检查依赖包")
    print("=" * 60)
    
    try:
        import requests
        print(f"✅ requests: {requests.__version__}")
    except ImportError:
        print("❌ requests: 未安装")
    
    try:
        import dotenv
        print(f"✅ python-dotenv: {dotenv.__version__}")
    except ImportError:
        print("❌ python-dotenv: 未安装")
    
    print("\n💡 安装依赖: pip install requests python-dotenv")

def check_network():
    """检查网络连接"""
    print("\n" + "=" * 60)
    print("4. 检查网络连接")
    print("=" * 60)
    
    test_urls = [
        ("GitHub API", "https://api.github.com"),
        ("GitHub", "https://github.com"),
        ("Google", "https://www.google.com"),
        ("百度", "https://www.baidu.com")
    ]
    
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {name}: 可访问 (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"❌ {name}: 连接超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: 连接失败")
        except Exception as e:
            print(f"❌ {name}: 错误 - {str(e)}")

def check_directory():
    """检查目录结构"""
    print("\n" + "=" * 60)
    print("5. 检查目录结构")
    print("=" * 60)
    
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    files = os.listdir(current_dir)
    print(f"目录内容: {files}")
    
    required_files = ["main.py", "config.py", ".env", "requirements.txt"]
    for file in required_files:
        if file in files:
            print(f"✅ {file}: 存在")
        else:
            print(f"❌ {file}: 不存在")

def main():
    """主函数"""
    print("🔍 Vless自动化脚本诊断工具")
    print("=" * 60)
    
    check_directory()
    check_env_file()
    check_python_version()
    check_dependencies()
    check_network()
    
    print("\n" + "=" * 60)
    print("📋 诊断完成")
    print("=" * 60)
    
    print("\n💡 建议:")
    print("1. 确保 .env 文件格式正确")
    print("2. 确保网络连接正常")
    print("3. 确保已安装所有依赖包")
    print("4. 运行: python main.py")

if __name__ == "__main__":
    main()