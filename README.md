# Vless节点自动化工作流

这是一个自动化的Python工作流，用于每日从GitHub仓库获取CSV文件，生成Vless节点，合并去重，并上传到GitHub。

## 功能特性

- ✅ 每日自动从GitHub获取CSV文件
- ✅ 自动解析CSV并生成Vless节点
- ✅ 下载现有远程节点
- ✅ 合并本地与远程节点并去重
- ✅ 生成双重Base64编码订阅
- ✅ 生成Clash YAML配置文件
- ✅ 自动上传到GitHub仓库
- ✅ 支持本地运行和GitHub Actions

## 部署方式

### 方式1: GitHub Actions (推荐)

1. **Fork仓库** 到你的GitHub账户

2. **添加密钥**:
   - 进入仓库 Settings → Secrets and variables → Actions
   - 点击 "New repository secret"
   - 添加 `PERSONAL_ACCESS_TOKEN`
     - 名称: `PERSONAL_ACCESS_TOKEN`
     - 值: 你的GitHub Personal Access Token (需要repo权限)

3. **配置目标仓库** (可选):
   在 `.github/workflows/daily.yml` 中修改:
   ```yaml
   env:
     GITHUB_REPO: 你的用户名/你的仓库名