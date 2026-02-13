#!/bin/bash

# 对话记忆和搜索功能演示脚本

echo "=============================================="
echo "  Claude 网页版 - 记忆和搜索功能演示"
echo "=============================================="
echo ""

# 检查应用是否运行
if ! pgrep -f "python.*app.py" > /dev/null; then
    echo "❌ 应用未运行，正在启动..."
    ./start.sh
    sleep 3
fi

echo "✓ 应用正在运行"
echo ""

# 检查数据库
if [ -f "conversations.db" ]; then
    echo "✓ 数据库文件存在: conversations.db"
    DB_SIZE=$(du -h conversations.db | cut -f1)
    echo "  数据库大小: $DB_SIZE"
else
    echo "❌ 数据库文件不存在"
    exit 1
fi
echo ""

# 运行测试
echo "运行功能测试..."
echo "----------------------------------------"
python3 test_memory.py
echo ""

# 显示功能说明
echo "=============================================="
echo "  功能说明"
echo "=============================================="
echo ""
echo "1. 对话持久化 💾"
echo "   - 所有对话自动保存到 SQLite 数据库"
echo "   - 刷新页面后自动加载历史记录"
echo "   - 支持跨会话访问"
echo ""
echo "2. 对话搜索 🔍"
echo "   - 点击右上角搜索图标"
echo "   - 输入关键词搜索历史对话"
echo "   - 搜索结果高亮显示"
echo ""
echo "3. 历史记录 📜"
echo "   - 点击右上角历史图标"
echo "   - 查看最近 100 条对话"
echo "   - 按时间倒序显示"
echo ""
echo "4. 清除历史 🗑️"
echo "   - 点击清除按钮"
echo "   - 永久删除所有历史记录"
echo ""
echo "=============================================="
echo "  访问应用"
echo "=============================================="
echo ""
echo "浏览器访问: http://localhost:5000"
echo ""
echo "登录信息:"
echo "  用户名: junner"
echo "  密码: xingfu@1984"
echo ""
echo "=============================================="
echo "  文档"
echo "=============================================="
echo ""
echo "详细说明: cat MEMORY_FEATURE.md"
echo "完整功能: cat FEATURES.md"
echo "快速参考: cat QUICK_REFERENCE.md"
echo ""
echo "祝使用愉快！🚀"
