#!/bin/bash
# GitHub 同步脚本

echo "=== Claude Web GitHub 同步 ==="
echo ""

# 检查 git 配置
echo "1. 检查 Git 配置..."
git config user.name "sunboygavin"
git config user.email "sunboygavin@users.noreply.github.com"
echo "✓ Git 用户配置完成"
echo ""

# 检查 gh CLI 认证
echo "2. 检查 GitHub CLI 认证..."
if gh auth status &>/dev/null; then
    echo "✓ 已认证"
else
    echo "需要认证，请运行: gh auth login"
    echo "选择: GitHub.com -> HTTPS -> Yes -> Login with a web browser"
    exit 1
fi
echo ""

# 创建或更新远程仓库
echo "3. 配置远程仓库..."
if git remote get-url origin &>/dev/null; then
    echo "远程仓库已存在"
    git remote -v
else
    # 检查仓库是否存在
    if gh repo view sunboygavin/claude-web &>/dev/null; then
        echo "仓库已存在，添加远程..."
        git remote add origin https://github.com/sunboygavin/claude-web.git
    else
        echo "创建新仓库..."
        gh repo create claude-web --public --source=. --remote=origin \
            --description "Claude Web - 功能完整版，基于 Flask 和 Anthropic API"
    fi
fi
echo ""

# 推送代码
echo "4. 推送代码到 GitHub..."
git branch -M main
git push -u origin main --force
echo ""

echo "=== 完成! ==="
echo "仓库地址: https://github.com/sunboygavin/claude-web"
