# Claude Web - 快速参考

## 🚀 快速启动
```bash
cd /root/claude-web
./start.sh
```
访问：http://localhost:5000

## 🔑 登录
- 用户名：`junner`
- 密码：`xingfu@1984`

## ⌨️ 命令速查

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/model` | 查看当前模型 |
| `/model sonnet` | 切换到 Sonnet |
| `/model opus` | 切换到 Opus |
| `/model haiku` | 切换到 Haiku |
| `/clear` | 清除历史 |
| `/tools` | 查看工具列表 |

## 🛠️ 可用工具（9个）

### 文件操作
- `bash` - 执行命令
- `read_file` - 读取文件
- `write_file` - 写入文件
- `edit_file` - 编辑文件
- `list_directory` - 列出目录

### 搜索
- `glob` - 文件模式匹配
- `grep` - 内容搜索

### 网络
- `web_fetch` - 获取网页
- `web_search` - 搜索网页

## 🎨 界面操作

### 右上角按钮
- 📋 下拉菜单 - 选择模型
- 🗑️ - 清除历史
- 💾 - 导出对话
- 退出 - 登出

### 左侧边栏
- 📁 文件浏览器
- 点击文件打开编辑器
- ◀ 折叠/展开侧边栏

## 💡 使用技巧

### 1. 快速切换模型
直接在右上角下拉菜单选择，无需输入命令

### 2. 查看工具
输入 `/tools` 查看所有可用工具及说明

### 3. 导出对话
点击 💾 按钮，自动下载 Markdown 文件

### 4. 清除历史
点击 🗑️ 按钮，确认后清空所有对话

### 5. 文件操作
- 左侧点击文件 → 打开编辑器
- 编辑后点击"保存"
- 点击"关闭"返回聊天

## 🤖 模型选择

| 模型 | 特点 | 适用场景 |
|------|------|---------|
| Sonnet 4.5 | 平衡 | 日常使用（默认） |
| Opus 4.6 | 最强 | 复杂任务 |
| Haiku 3.5 | 最快 | 简单任务 |

## 📝 示例对话

### 文件操作
```
读取 app.py 文件
```

### 搜索文件
```
查找所有 Python 文件
```

### 网页获取
```
获取 https://example.com 的内容
```

### 代码编写
```
帮我写一个 Python 函数计算斐波那契数列
```

## 🔧 故障排查

### 应用无法启动
```bash
./stop.sh
./start.sh
```

### 查看日志
```bash
tail -f /tmp/claude-0/-root-claude-web/tasks/*.output
```

### 重新安装依赖
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📚 更多信息
- 完整功能说明：`FEATURES.md`
- 升级说明：`UPGRADE_NOTES.md`
- 项目文档：`README.md`
