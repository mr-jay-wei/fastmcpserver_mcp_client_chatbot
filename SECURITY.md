# 安全配置指南

## 环境变量配置

1. **复制环境变量模板**：
   ```bash
   cp .env.example .env
   ```

2. **编辑 .env 文件**，填入你的真实 API 密钥：
   ```bash
   # 编辑 .env 文件
   notepad .env  # Windows
   # 或
   nano .env     # Linux/Mac
   ```

3. **配置 MCP 设置文件**：
   - 复制 `fastmcp_server_Cline/cline_mcp_settings.txt` 
   - 将其中的占位符替换为真实的 API 密钥

## 重要提醒

- ⚠️ **绝对不要**将真实的 API 密钥提交到 Git
- ✅ 使用 `.env` 文件管理敏感信息
- ✅ 确保 `.env` 文件在 `.gitignore` 中
- ✅ 只提交 `.env.example` 模板文件

## API 密钥获取

- **GitHub Token**: https://github.com/settings/tokens
- **Kimi API**: https://platform.moonshot.cn/
- **Firecrawl API**: https://firecrawl.dev/

## 如果意外泄露了密钥

1. 立即撤销/重新生成 API 密钥
2. 使用 `git reset` 从历史中移除敏感信息
3. 强制推送更新远程仓库