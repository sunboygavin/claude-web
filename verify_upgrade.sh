#!/bin/bash
# 验证 Claude Web 升级是否成功

echo "=================================="
echo "Claude Web 升级验证"
echo "=================================="
echo ""

# 检查文件
echo "📁 检查文件..."
files=(
    "app.py"
    "config.py"
    "tools.py"
    "static/js/script.js"
    "templates/index.html"
    "static/css/style.css"
    "requirements.txt"
    "FEATURES.md"
    "QUICK_REFERENCE.md"
    "SUMMARY.md"
    "test_features.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
    fi
done
echo ""

# 检查依赖
echo "📦 检查依赖..."
source venv/bin/activate
if pip list | grep -q "requests"; then
    echo "  ✓ requests"
else
    echo "  ✗ requests (未安装)"
fi

if pip list | grep -q "beautifulsoup4"; then
    echo "  ✓ beautifulsoup4"
else
    echo "  ✗ beautifulsoup4 (未安装)"
fi
echo ""

# 检查配置
echo "⚙️  检查配置..."
if grep -q "AVAILABLE_MODELS" config.py; then
    echo "  ✓ 模型配置已添加"
else
    echo "  ✗ 模型配置缺失"
fi

if grep -q "DEFAULT_MODEL" config.py; then
    echo "  ✓ 默认模型已设置"
else
    echo "  ✗ 默认模型缺失"
fi
echo ""

# 检查工具
echo "🛠️  检查工具..."
if grep -q "web_fetch" tools.py; then
    echo "  ✓ web_fetch 工具已添加"
else
    echo "  ✗ web_fetch 工具缺失"
fi

if grep -q "web_search" tools.py; then
    echo "  ✓ web_search 工具已添加"
else
    echo "  ✗ web_search 工具缺失"
fi
echo ""

# 检查 API
echo "🌐 检查 API..."
if grep -q "/api/model" app.py; then
    echo "  ✓ /api/model 接口已添加"
else
    echo "  ✗ /api/model 接口缺失"
fi

if grep -q "/api/clear" app.py; then
    echo "  ✓ /api/clear 接口已添加"
else
    echo "  ✗ /api/clear 接口缺失"
fi

if grep -q "/api/export" app.py; then
    echo "  ✓ /api/export 接口已添加"
else
    echo "  ✗ /api/export 接口缺失"
fi
echo ""

# 检查前端
echo "💻 检查前端..."
if grep -q "modelSelector" static/js/script.js; then
    echo "  ✓ 模型选择器已添加"
else
    echo "  ✗ 模型选择器缺失"
fi

if grep -q "clearHistory" static/js/script.js; then
    echo "  ✓ 清除历史功能已添加"
else
    echo "  ✗ 清除历史功能缺失"
fi

if grep -q "exportConversation" static/js/script.js; then
    echo "  ✓ 导出功能已添加"
else
    echo "  ✗ 导出功能缺失"
fi
echo ""

# 检查应用状态
echo "🚀 检查应用状态..."
if ps aux | grep -q "[p]ython app.py"; then
    echo "  ✓ 应用正在运行"

    # 检查端口
    if curl -s http://localhost:5000/login > /dev/null 2>&1; then
        echo "  ✓ 端口 5000 可访问"
    else
        echo "  ✗ 端口 5000 无法访问"
    fi
else
    echo "  ⚠ 应用未运行（运行 ./start.sh 启动）"
fi
echo ""

# 运行功能测试
echo "🧪 运行功能测试..."
python test_features.py > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ 功能测试通过"
else
    echo "  ✗ 功能测试失败"
    echo "  查看详情: cat /tmp/test_output.txt"
fi
echo ""

# 总结
echo "=================================="
echo "✅ 验证完成！"
echo "=================================="
echo ""
echo "📖 查看文档："
echo "  - FEATURES.md - 完整功能说明"
echo "  - QUICK_REFERENCE.md - 快速参考"
echo "  - SUMMARY.md - 升级总结"
echo ""
echo "🚀 访问应用："
echo "  http://localhost:5000"
echo ""
echo "🔑 登录信息："
echo "  用户名: junner"
echo "  密码: xingfu@1984"
echo ""
