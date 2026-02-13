# Claude Web 工具快速参考

## 工具列表

### 1. bash - 执行命令
```python
bash(
    command="git status",           # 必需：要执行的命令
    description="Check git status", # 可选：命令描述
    timeout=120000                  # 可选：超时（毫秒），默认 120000，最大 600000
)
```

**注意**: 不要用 bash 进行文件操作，使用专用工具。

### 2. read_file - 读取文件
```python
read_file(
    file_path="/path/to/file.py",  # 必需：文件路径
    offset=0,                       # 可选：起始行号
    limit=100                       # 可选：读取行数
)
```

**特性**:
- 自动添加行号
- 支持最大 10MB 文件
- 默认限制 2000 行
- 返回总行数信息

### 3. write_file - 写入文件
```python
write_file(
    file_path="/path/to/file.py",  # 必需：文件路径
    content="print('hello')"        # 必需：文件内容
)
```

**特性**:
- 自动创建目录
- 覆盖现有文件

### 4. edit_file - 编辑文件
```python
edit_file(
    file_path="/path/to/file.py",  # 必需：文件路径
    old_string="old_var",           # 必需：要替换的文本
    new_string="new_var",           # 必需：新文本
    replace_all=False               # 可选：是否替换所有出现
)
```

**特性**:
- 精确字符串替换
- 默认要求唯一匹配
- replace_all=True 可批量替换
- 返回替换次数

### 5. glob - 文件模式匹配
```python
glob(
    pattern="**/*.py",              # 必需：glob 模式
    path="/root/claude-web"         # 可选：搜索路径
)
```

**示例模式**:
- `*.py` - 当前目录的 Python 文件
- `**/*.py` - 递归查找所有 Python 文件
- `src/**/*.{js,ts}` - src 下的 JS 和 TS 文件

### 6. grep - 内容搜索
```python
grep(
    pattern="def.*test",                    # 必需：正则表达式
    path="/root/claude-web",                # 可选：搜索路径
    file_pattern="*.py",                    # 可选：文件过滤
    case_insensitive=False,                 # 可选：大小写不敏感
    output_mode="files_with_matches",       # 可选：输出模式
    context=3,                              # 可选：上下文行数
    head_limit=100                          # 可选：结果限制
)
```

**输出模式**:
- `files_with_matches` - 仅文件路径（默认）
- `content` - 匹配行内容
- `count` - 每个文件的匹配数

**示例**:
```python
# 查找包含 "TODO" 的文件
grep(pattern="TODO", output_mode="files_with_matches")

# 查看匹配内容和上下文
grep(pattern="def test", output_mode="content", context=3)

# 统计匹配数量
grep(pattern="import", output_mode="count")

# 大小写不敏感搜索
grep(pattern="error", case_insensitive=True)
```

### 7. list_directory - 列出目录
```python
list_directory(
    path="/root/claude-web"         # 必需：目录路径
)
```

**返回**:
- 文件和目录列表
- 类型（file/directory）
- 文件大小

### 8. web_fetch - 获取网页
```python
web_fetch(
    url="https://example.com",      # 必需：URL
    prompt="Extract main content"   # 必需：提取指令
)
```

**特性**:
- 自动解析 HTML
- 移除脚本和样式
- 限制 5000 字符

### 9. web_search - 网页搜索
```python
web_search(
    query="Python best practices"  # 必需：搜索查询
)
```

**特性**:
- 使用 DuckDuckGo
- 返回前 5 个结果
- 包含标题、URL、摘要

## 使用场景

### 场景 1: 查找和修改代码
```python
# 1. 查找包含特定函数的文件
grep(pattern="def process_data", output_mode="files_with_matches")

# 2. 读取文件
read_file(file_path="/path/to/file.py")

# 3. 编辑文件
edit_file(
    file_path="/path/to/file.py",
    old_string="old_function_name",
    new_string="new_function_name",
    replace_all=True
)
```

### 场景 2: 分析大文件
```python
# 1. 读取前 100 行
read_file(file_path="/path/to/large.log", limit=100)

# 2. 读取中间部分
read_file(file_path="/path/to/large.log", offset=1000, limit=100)

# 3. 搜索特定内容
grep(
    pattern="ERROR",
    path="/path/to/large.log",
    output_mode="content",
    context=2
)
```

### 场景 3: 项目分析
```python
# 1. 列出项目结构
list_directory(path="/root/claude-web")

# 2. 查找所有 Python 文件
glob(pattern="**/*.py")

# 3. 统计函数定义
grep(pattern="^def ", output_mode="count", file_pattern="*.py")

# 4. 查找 TODO 注释
grep(pattern="TODO|FIXME", output_mode="content")
```

### 场景 4: Git 操作
```python
# 1. 查看状态
bash(command="git status")

# 2. 查看差异
bash(command="git diff", timeout=30000)

# 3. 提交更改
bash(command='git add . && git commit -m "Update"')

# 4. 推送（长时间操作）
bash(command="git push", timeout=300000)
```

## 最佳实践

### 文件操作
1. **先读后写** - 编辑前先用 read_file 查看内容
2. **使用分页** - 大文件使用 offset 和 limit
3. **精确替换** - edit_file 提供足够的上下文确保唯一性
4. **批量操作** - 重命名变量时使用 replace_all=True

### 搜索操作
1. **选择模式** - 根据需求选择合适的 output_mode
2. **过滤文件** - 使用 file_pattern 缩小搜索范围
3. **限制结果** - 使用 head_limit 避免输出过多
4. **添加上下文** - 使用 context 参数查看周围代码

### 命令执行
1. **设置超时** - 长时间命令设置合适的 timeout
2. **添加描述** - 使用 description 说明命令用途
3. **避免交互** - 不要使用需要用户输入的命令
4. **检查输出** - 注意 return_code 和 stderr

### 性能优化
1. **并行搜索** - 多个独立搜索可以并行执行
2. **缓存结果** - 重复读取的文件可以缓存
3. **限制范围** - 指定具体路径而不是全局搜索
4. **使用 glob** - 先用 glob 找文件，再用 grep 搜内容

## 错误处理

所有工具返回格式：
```python
{
    "success": True/False,
    "error": "错误信息",      # 失败时
    # ... 其他结果字段
}
```

常见错误：
- `File not found` - 文件不存在
- `File too large` - 文件超过大小限制
- `old_string not found` - 编辑时找不到目标字符串
- `Command timed out` - 命令执行超时
- `Permission denied` - 权限不足

## 安全注意事项

1. **路径验证** - 所有路径都会转换为绝对路径
2. **文件大小** - read_file 限制 10MB
3. **超时保护** - bash 命令最长 10 分钟
4. **结果限制** - grep 和 glob 限制结果数量
5. **错误隔离** - 工具错误不会影响其他操作

## 版本信息

- **版本**: 2.2.0
- **更新日期**: 2026-02-12
- **兼容性**: 向后兼容 2.1.0

## 更多信息

- 完整文档: [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)
- 功能说明: [FEATURES.md](FEATURES.md)
- 使用指南: [README.md](README.md)
