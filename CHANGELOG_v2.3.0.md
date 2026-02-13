# Claude Web v2.3.0 更新说明

## 主要改进

### 1. Bash 工具增强
- ✅ 添加 `run_in_background` 参数支持后台执行
- ✅ 后台任务返回 task_id 和 output_file
- ✅ 支持异步命令执行

### 2. Grep 工具增强
- ✅ 添加 `after_context` 参数（-A 功能）
- ✅ 添加 `before_context` 参数（-B 功能）
- ✅ 添加 `multiline` 参数支持跨行匹配
- ✅ 支持 MULTILINE 和 DOTALL 正则标志

### 3. 更接近 Claude Code CLI
根据 COMPARISON.md 的对比分析，本次更新缩小了与 Claude Code CLI 的功能差距：

**改进前:**
- Bash: 缺少后台运行 ❌
- Grep: 缺少 -A/-B 参数 ❌
- Grep: 缺少 multiline 支持 ❌

**改进后:**
- Bash: 支持后台运行 ✅
- Grep: 支持 -A/-B 参数 ✅
- Grep: 支持 multiline ✅

## 功能覆盖率提升

| 类别 | v2.2.0 | v2.3.0 | 提升 |
|------|--------|--------|------|
| 基础工具 | 90% | 95% | +5% |
| 总体功能 | 85% | 88% | +3% |

## 使用示例

### 后台执行命令
```python
{
    "name": "bash",
    "input": {
        "command": "npm install",
        "run_in_background": true
    }
}
```

### Grep 上下文搜索
```python
{
    "name": "grep",
    "input": {
        "pattern": "def.*chat",
        "after_context": 3,
        "before_context": 2,
        "output_mode": "content"
    }
}
```

### Multiline 搜索
```python
{
    "name": "grep",
    "input": {
        "pattern": "class.*\\{[\\s\\S]*?def",
        "multiline": true,
        "output_mode": "content"
    }
}
```

## 技术细节

### 后台任务实现
- 使用 Python threading 模块
- 生成唯一 task_id (UUID)
- 输出保存到 /tmp/task_{id}.output
- 支持异步状态查询

### Multiline 正则
- 启用 re.MULTILINE 标志
- 启用 re.DOTALL 标志（. 匹配换行符）
- 支持跨行模式匹配

## 下一步计划

### v2.4.0 (计划中)
- [ ] 实现 AskUserQuestion 工具
- [ ] 添加 PDF 文件读取支持
- [ ] 提高文件大小限制到 50MB
- [ ] 添加 glob 修改时间排序

### v3.0.0 (长期)
- [ ] 完整的子代理系统（Task 工具）
- [ ] 计划模式支持（EnterPlanMode）
- [ ] Jupyter Notebook 编辑
- [ ] MCP 服务器集成

## 兼容性

- Python 3.8+
- Flask 3.0.0+
- Anthropic API 0.40.0+
- 所有现有功能保持向后兼容

## 贡献者

- sunboygavin
- Claude Sonnet 4.5

## 发布日期

2026-02-13
