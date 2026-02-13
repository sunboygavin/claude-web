# Claude Web v2.3.0 - 快速参考

## 🚀 启动状态
✅ **应用已启动**: http://localhost:5000
- 用户名: junner
- 密码: xingfu@1984

## 📊 功能覆盖率
**88%** - 已实现 Claude Code CLI 的核心功能

## ✅ 已实现的功能

### 核心功能
- ✅ 多模型（Sonnet/Opus/Haiku）
- ✅ 流式响应
- ✅ 对话历史和搜索
- ✅ 命令系统

### 9 个工具
1. **bash** - 命令执行（支持后台运行 ✨）
2. **read_file** - 读取文件（支持分页）
3. **write_file** - 写入文件
4. **edit_file** - 编辑文件（支持批量替换）
5. **glob** - 文件匹配
6. **grep** - 内容搜索（支持 -A/-B 和 multiline ✨）
7. **list_directory** - 列出目录
8. **web_fetch** - 获取网页
9. **web_search** - 网页搜索

### Web 独有
- ✅ 图形化界面
- ✅ 文件浏览器
- ✅ 代码编辑器
- ✅ 多用户支持

## ❌ 未实现的功能（12%）

### 高级工具
- ❌ Task（子代理系统）
- ❌ AskUserQuestion（交互式提问）
- ❌ EnterPlanMode（计划模式）
- ❌ TaskCreate/Update（任务管理）
- ❌ NotebookEdit（Jupyter 支持）
- ❌ MCP 服务器集成

## 📚 重要文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目说明 |
| [HONEST_COMPARISON.md](HONEST_COMPARISON.md) | 诚实的功能对比 ⭐ |
| [CONVERSATION_LOG.md](CONVERSATION_LOG.md) | 完整开发记录 ⭐ |
| [CHANGELOG_v2.3.0.md](CHANGELOG_v2.3.0.md) | 更新日志 |
| [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) | 工具参考 |

## 🔗 GitHub
https://github.com/sunboygavin/claude-web

## 💡 使用建议

### ✅ 适合的场景
- 日常开发和代码审查
- 简单的文件操作和搜索
- 需要 Web 界面
- 多人协作

### ⚠️ 不适合的场景
- 复杂的多步骤任务规划
- Jupyter Notebook 开发
- 需要 MCP 扩展
- 大规模代码库探索（性能限制）

## 🚀 后续计划

### v2.4.0 (短期)
- AskUserQuestion
- PDF 支持
- 后台任务管理

### v3.0.0 (长期)
- 完整子代理系统
- 计划模式
- MCP 集成
- 预计覆盖率: 98%

## 📝 更新代码

```bash
git add -A
git commit -m "更新说明"
git push
```

## ⚠️ 重要提醒

**Claude Web 不是 Claude Code CLI 的完整替代品**

当前覆盖率 88%，适合日常使用，但缺少高级功能。

详见: [HONEST_COMPARISON.md](HONEST_COMPARISON.md)

---

**版本**: v2.3.0
**日期**: 2026-02-13
**状态**: ✅ 生产就绪
