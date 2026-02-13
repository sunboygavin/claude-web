# Claude Web - 功能完整版

基于 Flask 和 Anthropic API 的 Claude 聊天界面，完整实现 Claude Code CLI 的核心功能。

## 功能特性

### 核心功能
- 现代化的聊天界面
- 实时流式响应
- 对话历史记录（持久化）
- 对话搜索功能
- 用户登录认证
- 文件浏览器（左侧边栏）
- 代码编辑器

### Claude Code 功能
- **多模型支持**
  - Claude Sonnet 4.5（平衡）
  - Claude Opus 4.6（最强）
  - Claude Haiku 3.5（最快）

- **命令系统**
  - `/help` - 显示帮助信息
  - `/model` - 模型管理
  - `/clear` - 清除对话历史
  - `/export` - 导出对话
  - `/tools` - 查看工具列表

- **9 个强大工具**
  - `bash` - 执行 bash 命令（支持后台运行）
  - `read_file` - 读取文件内容（支持分页）
  - `write_file` - 创建/覆盖文件
  - `edit_file` - 编辑文件（支持批量替换）
  - `glob` - 文件模式匹配
  - `grep` - 内容搜索（支持 -A/-B 参数和 multiline）
  - `list_directory` - 列出目录
  - `web_fetch` - 获取网页内容
  - `web_search` - 网页搜索

## 快速开始

### 1. 安装依赖
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置
复制 `config.py.example` 并修改配置:
```bash
cp config.py.example config.py
# 编辑 config.py 设置 API 密钥
```

### 3. 启动应用
```bash
chmod +x start.sh
./start.sh
```

### 4. 访问应用
打开浏览器访问：**http://localhost:5000**

### 5. 停止应用
```bash
./stop.sh
```

## 技术栈

- **后端**: Flask 3.0.0 + Anthropic API 0.40.0
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **数据库**: SQLite 3（对话持久化）
- **模型**: Claude Sonnet 4.5 / Opus 4.6 / Haiku 3.5

## 项目结构

```
claude-web/
├── app.py                    # Flask 主应用
├── config.py                 # 配置文件
├── tools.py                  # 工具定义
├── database.py               # 数据库操作
├── system_prompt.py          # 系统提示词
├── requirements.txt          # Python 依赖
├── start.sh / stop.sh        # 启动/停止脚本
├── static/
│   ├── css/style.css        # 样式表
│   └── js/script.js         # 前端逻辑
└── templates/
    ├── login.html           # 登录页面
    └── index.html           # 主界面
```

## 文档

- [FEATURES.md](FEATURES.md) - 完整功能说明
- [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) - 工具快速参考
- [COMPARISON.md](COMPARISON.md) - 与 Claude Code CLI 对比
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速参考卡片

## 安全说明

- 文件访问限制在项目目录内
- 文件类型和大小有限制
- Session 使用 SECRET_KEY 加密
- 支持的文件类型：.py, .js, .html, .css, .json, .txt, .md, .yml, .yaml, .sh

## 版本信息

- **当前版本**: 2.3.0
- **发布日期**: 2026-02-13
- **状态**: 生产就绪

## 更新日志

### v2.3.0 (2026-02-13)
- ✅ 添加 bash 后台运行支持（run_in_background）
- ✅ 添加 grep 的 -A/-B 参数（after_context/before_context）
- ✅ 添加 multiline 搜索支持
- ✅ 更接近 Claude Code CLI 的功能

### v2.2.0 (2026-02-12)
- ✅ 工具功能大幅增强
- ✅ 添加系统提示词指导
- ✅ 数据库连接池和事务优化

## 许可

MIT License
