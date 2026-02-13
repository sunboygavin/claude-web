# Claude Web 项目文件清单

## 📁 核心文件

### 后端
- `app.py` - Flask 主应用（已升级）
- `config.py` - 配置文件（已升级）
- `tools.py` - 工具定义（已升级）
- `requirements.txt` - Python 依赖（已升级）

### 前端
- `templates/index.html` - 主界面（已升级）
- `templates/login.html` - 登录页面
- `static/js/script.js` - 前端逻辑（已升级）
- `static/css/style.css` - 样式表（已升级）

### 脚本
- `start.sh` - 启动脚本
- `stop.sh` - 停止脚本
- `demo.sh` - 演示脚本（新增）
- `verify_upgrade.sh` - 验证脚本（新增）
- `test_features.py` - 功能测试（新增）

## 📚 文档文件

### 主要文档
- `README.md` - 项目说明（已更新）
- `FEATURES.md` - 完整功能说明（新增）
- `QUICK_REFERENCE.md` - 快速参考（新增）
- `SUMMARY.md` - 升级总结（新增）
- `UPGRADE_NOTES.md` - 升级说明（新增）
- `PROJECT_FILES.md` - 本文件（新增）

## 🔧 配置文件

### Python 环境
- `venv/` - 虚拟环境目录
- `__pycache__/` - Python 缓存

### IDE 配置
- `.claude/` - Claude IDE 配置

## 📊 文件统计

### 代码文件
- Python: 3 个（app.py, config.py, tools.py）
- JavaScript: 1 个（script.js）
- HTML: 2 个（index.html, login.html）
- CSS: 1 个（style.css）

### 文档文件
- Markdown: 6 个
- Shell: 4 个

### 总计
- 核心文件: 11 个
- 文档文件: 10 个
- 总文件数: 21 个

## 🎯 关键改动

### v2.0.0 升级
1. **config.py**
   - 添加 AVAILABLE_MODELS
   - 添加 DEFAULT_MODEL

2. **app.py**
   - 添加 /api/model 接口
   - 添加 /api/clear 接口
   - 添加 /api/export 接口
   - 添加 handle_command() 函数
   - 支持动态模型切换

3. **tools.py**
   - 添加 web_fetch 工具
   - 添加 web_search 工具
   - 导入 requests 和 BeautifulSoup

4. **script.js**
   - 添加 loadCurrentModel()
   - 添加 changeModel()
   - 添加 clearHistory()
   - 添加 exportConversation()
   - 添加 handleCommand()
   - 添加 formatMarkdown()

5. **index.html**
   - 添加模型选择器
   - 添加清除按钮
   - 添加导出按钮
   - 添加命令提示

6. **style.css**
   - 添加 .model-selector 样式
   - 添加 .action-btn 样式
   - 添加 .command-hint 样式
   - 添加 .command-response 样式
   - 添加 .message.system 样式

7. **requirements.txt**
   - 添加 requests==2.31.0
   - 添加 beautifulsoup4==4.12.2

## 📝 使用说明

### 查看文档
```bash
cat README.md              # 项目说明
cat FEATURES.md            # 完整功能
cat QUICK_REFERENCE.md     # 快速参考
cat SUMMARY.md             # 升级总结
```

### 运行脚本
```bash
./start.sh                 # 启动应用
./stop.sh                  # 停止应用
./demo.sh                  # 查看演示
./verify_upgrade.sh        # 验证升级
python test_features.py    # 功能测试
```

### 编辑文件
```bash
vim app.py                 # 编辑主应用
vim config.py              # 编辑配置
vim tools.py               # 编辑工具
vim static/js/script.js    # 编辑前端
```

## 🔍 文件依赖关系

```
app.py
├── config.py (配置)
├── tools.py (工具)
└── templates/
    ├── index.html
    │   ├── static/js/script.js
    │   └── static/css/style.css
    └── login.html

tools.py
├── requests (HTTP)
└── beautifulsoup4 (HTML 解析)

script.js
└── index.html (DOM 操作)
```

## ✅ 完整性检查

所有核心文件已就位：
- [x] app.py
- [x] config.py
- [x] tools.py
- [x] requirements.txt
- [x] templates/index.html
- [x] templates/login.html
- [x] static/js/script.js
- [x] static/css/style.css
- [x] start.sh
- [x] stop.sh

所有文档文件已创建：
- [x] README.md
- [x] FEATURES.md
- [x] QUICK_REFERENCE.md
- [x] SUMMARY.md
- [x] UPGRADE_NOTES.md
- [x] PROJECT_FILES.md

所有测试脚本已创建：
- [x] test_features.py
- [x] verify_upgrade.sh
- [x] demo.sh

## 🎉 项目状态

**版本**: 2.0.0
**状态**: ✅ 生产就绪
**功能**: 完整
**文档**: 完善
**测试**: 通过

---

*最后更新: 2026-02-11*
