# GitHub 仓库创建指南

## 步骤 1: 在 GitHub 上创建仓库

1. 访问: https://github.com/new
2. 填写信息:
   - Repository name: `claude-web`
   - Description: `Claude Web - 功能完整版，基于 Flask 和 Anthropic API 的 Claude 聊天界面`
   - 选择: **Public**
   - **不要**勾选 "Add a README file"
   - **不要**勾选 "Add .gitignore"
   - **不要**勾选 "Choose a license"
3. 点击 "Create repository"

## 步骤 2: 推送代码

创建仓库后，在本地运行:

```bash
cd /root/claude-web
git push -u origin main
```

## 或者使用一键脚本

```bash
# 方式 1: 使用 GitHub API 创建仓库
curl -X POST -H "Authorization: token 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" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{"name":"claude-web","description":"Claude Web - 功能完整版，基于 Flask 和 Anthropic API 的 Claude 聊天界面","private":false}'

# 然后推送
git push -u origin main
```

## 验证

推送成功后，访问:
https://github.com/sunboygavin/claude-web

## 后续更新

每次更新代码后:

```bash
git add -A
git commit -m "更新说明"
git push
```
