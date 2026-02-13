#!/bin/bash
# 推送到 GitHub 的脚本

TOKEN="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"

echo "=== 推送代码到 GitHub ==="
echo ""

# 配置远程仓库（包含 token）
git remote remove origin 2>/dev/null
git remote add origin https://${TOKEN}@github.com/sunboygavin/claude-web.git

echo "✓ 远程仓库已配置"
echo ""

# 推送代码
echo "正在推送..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=== 推送成功! ==="
    echo "仓库地址: https://github.com/sunboygavin/claude-web"
    echo ""

    # 清理 token（安全考虑）
    git remote remove origin
    git remote add origin https://github.com/sunboygavin/claude-web.git
    echo "✓ 已清理 token，后续推送请使用 SSH 或重新配置"
else
    echo ""
    echo "=== 推送失败 ==="
    echo "请检查:"
    echo "1. 仓库是否已创建"
    echo "2. Token 是否有效"
    echo "3. 网络连接是否正常"
fi
