#!/usr/bin/env python3
"""
调试脚本 - 检查环境变量加载
"""
import os
import sys
from dotenv import load_dotenv

print("=" * 50)
print("环境变量调试")
print("=" * 50)

# 显示当前目录
print(f"当前目录: {os.getcwd()}")

# 检查 .env 文件
env_file = ".env"
print(f"检查文件: {env_file}")

if os.path.exists(env_file):
    print("✅ 找到 .env 文件")
    
    # 读取文件内容
    with open(env_file, "r") as f:
        content = f.read()
        print(f"文件内容:\n{content}")
else:
    print("❌ 未找到 .env 文件")
    
    # 创建示例文件
    create = input("是否创建示例 .env 文件? (y/n): ")
    if create.lower() == 'y':
        with open(env_file, "w") as f:
            f.write("GITHUB_TOKEN=你的GitHub令牌\n")
            f.write("GITHUB_REPO=DaiZhouHui/CustomNode\n")
            f.write("GITHUB_BRANCH=main\n")
        print("✅ 已创建 .env 文件，请编辑它并填入实际值")

# 加载 .env 文件
print("\n加载 .env 文件...")
load_dotenv()

# 检查环境变量
print("\n检查环境变量:")
print(f"GITHUB_TOKEN: {os.getenv('GITHUB_TOKEN', '未设置')}")
print(f"GITHUB_REPO: {os.getenv('GITHUB_REPO', '未设置')}")
print(f"GITHUB_BRANCH: {os.getenv('GITHUB_BRANCH', '未设置')}")

# 检查其他环境变量
print("\n所有环境变量:")
for key, value in os.environ.items():
    if "GITHUB" in key or "TOKEN" in key:
        print(f"{key}: {value}")

print("=" * 50)