# Auto-Approve 自动批准功能

## 功能概述

网页版Claude Code现已支持auto-approve（自动批准）模式，允许用户选择是否自动批准工具调用。

## 使用方法

### 1. 页面开关

在页面顶部header区域，模型选择器旁边有一个"自动批准"开关：

```
[Sonnet 4.5 ▼] [☑ 自动批准] [🔍] [📜] [📋] [🗑️] [💾]
```

- **勾选**：启用auto-approve模式
- **不勾选**：需要手动批准敏感操作

### 2. 工作原理

#### Auto-Approve = False（默认）
- 敏感操作（如git push、文件删除等）会触发权限请求
- 用户需要在页面上点击"批准"或"拒绝"
- Claude可能会主动调用`ask_user_question`征求意见

#### Auto-Approve = True
- 权限系统的请求会自动批准
- 跳过`pending_permission`状态
- **注意**：Claude仍可能主动调用`ask_user_question`

## 技术实现

### 前端（JavaScript）

```javascript
// 获取auto_approve设置
const autoApprove = document.getElementById('autoApproveToggle').checked;

// 发送到后端
body: JSON.stringify({
    message: message,
    history: conversationHistory.slice(0, -1),
    auto_approve: autoApprove
})
```

### 后端（Python）

```python
# 接收参数
auto_approve = data.get('auto_approve', False)

# 传递给工具路由
exec_result = tool_router.execute_tool(
    tool_name=tool_name,
    tool_input=tool_input,
    username=username,
    session_id=session_id,
    auto_approve=auto_approve
)
```

### 工具路由（tool_router.py）

```python
def execute_tool(self, tool_name: str, tool_input: Dict[str, Any],
                 username: str, session_id: str,
                 auto_approve: bool = False) -> Dict[str, Any]:

    requires_permission = check_requires_permission(tool_name, tool_input)

    if requires_permission and not auto_approve:
        # 返回pending状态，等待用户批准
        return {
            'status': 'pending_permission',
            'log_id': log_id,
            'preview': preview
        }

    # auto_approve=True时直接执行
    result = self._execute_tool(tool_name, tool_input)
    return {'status': 'success', 'result': result}
```

## 安全考虑

### 两层保护机制

1. **权限系统**（可被auto-approve跳过）
   - 检查工具和参数是否需要权限
   - `auto_approve=true`时自动批准

2. **Claude主动询问**（不受auto-approve影响）
   - Claude可以主动调用`ask_user_question`
   - 即使`auto_approve=true`，Claude仍可能询问
   - 这是AI安全的最佳实践

### 推荐使用场景

**适合启用auto-approve：**
- 开发测试环境
- 信任的自动化任务
- 重复性操作

**不建议启用auto-approve：**
- 生产环境
- 敏感数据操作
- 不熟悉的代码库

## 测试验证

### 测试1：基本工具调用
```bash
# auto_approve=false
curl -X POST http://localhost:5000/api/chat \
  -d '{"message":"执行ls命令","auto_approve":false}'
# 结果：正常执行，无需批准（ls不是敏感操作）
```

### 测试2：Git推送操作
```bash
# auto_approve=false
curl -X POST http://localhost:5000/api/chat \
  -d '{"message":"推送代码到github","auto_approve":false}'
# 结果：Claude调用ask_user_question请求确认
```

### 测试3：Auto-Approve模式
```bash
# auto_approve=true
curl -X POST http://localhost:5000/api/chat \
  -d '{"message":"推送代码到github","auto_approve":true}'
# 结果：权限系统自动批准，但Claude仍可能询问
```

## Agentic Loop

配合完整的agentic loop实现，auto-approve模式可以让Claude：

1. 持续执行工具直到任务完成（最多25轮）
2. 自动批准权限请求
3. 无需人工干预完成复杂任务

### 示例流程

```
用户：把test.txt推送到github
↓
Claude: git status (自动执行)
↓
Claude: git add test.txt (auto_approve=true，自动批准)
↓
Claude: git commit -m "..." (auto_approve=true，自动批准)
↓
Claude: git push (auto_approve=true，自动批准)
↓
完成！
```

## 相关文件

- `templates/index.html` - 页面UI和开关
- `static/css/style.css` - 开关样式
- `static/js/script.js` - 前端逻辑
- `app.py` - 后端API
- `tool_router.py` - 工具路由和权限检查
- `operation_logger.py` - 操作日志

## 更新日志

- 2026-02-13: 添加auto-approve功能
- 2026-02-13: 实现完整的agentic loop
- 2026-02-13: 修复工具调用链中断问题
