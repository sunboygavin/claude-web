# Claude Web 升级说明

## 新增功能

### 1. 模型选择功能
- 支持在 Sonnet 4.5、Opus 4.6 和 Haiku 3.5 之间切换
- 界面右上角添加了模型选择下拉菜单
- 模型选择会保存在会话中

### 2. 命令系统
支持以下命令：

- `/help` - 显示帮助信息
- `/model [sonnet|opus|haiku]` - 切换模型或查看当前模型
- `/clear` - 清除对话历史
- `/export` - 导出对话历史
- `/tools` - 查看可用工具列表

### 3. 会话管理
- **清除历史**: 点击 🗑️ 按钮清除所有对话历史
- **导出对话**: 点击 💾 按钮导出对话为 Markdown 文件

### 4. 新增工具
- **web_fetch**: 获取网页内容并提取文本
- **web_search**: 搜索网页（使用 DuckDuckGo）

### 5. 界面改进
- 添加了命令提示
- 改进了消息显示样式
- 添加了系统消息类型
- 优化了工具调用的可视化

## 安装步骤

1. 安装新依赖：
```bash
pip install -r requirements.txt
```

2. 重启应用：
```bash
./stop.sh
./start.sh
```

## 使用示例

### 切换模型
```
/model opus
```

### 查看帮助
```
/help
```

### 清除历史
点击界面右上角的 🗑️ 按钮

### 导出对话
点击界面右上角的 💾 按钮

### 使用新工具
直接向 Claude 提问，它会自动调用相应的工具：

- "帮我搜索 Python 最新版本"（会使用 web_search）
- "获取这个网页的内容：https://example.com"（会使用 web_fetch）

## 技术细节

### 后端改动
- `app.py`: 添加了 `/api/model`、`/api/clear`、`/api/export` 接口
- `app.py`: 添加了 `handle_command()` 函数处理命令
- `tools.py`: 添加了 `web_fetch` 和 `web_search` 工具
- `config.py`: 添加了模型配置

### 前端改动
- `script.js`: 添加了模型切换、清除历史、导出对话功能
- `script.js`: 添加了命令处理逻辑
- `index.html`: 添加了模型选择器和操作按钮
- `style.css`: 添加了新组件的样式

## 注意事项

1. Web 搜索功能使用 DuckDuckGo，可能会受到网络限制
2. Web 获取功能有 5000 字符的内容限制
3. 模型选择会保存在会话中，刷新页面后需要重新选择
4. 导出的对话文件为 Markdown 格式

## 未来改进

- [ ] 添加更多模型选项
- [ ] 支持自定义系统提示词
- [ ] 添加代码高亮显示
- [ ] 支持图片上传和分析
- [ ] 添加对话搜索功能
- [ ] 支持多会话管理
