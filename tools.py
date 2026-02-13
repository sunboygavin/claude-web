import os
import subprocess
import glob as glob_module
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# 工具定义
TOOLS = [
    {
        "name": "bash",
        "description": "Executes a bash command with optional timeout. Use this for terminal operations like git, npm, docker, etc. DO NOT use for file operations (reading, writing, editing, searching) - use specialized tools instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "description": {
                    "type": "string",
                    "description": "Clear, concise description of what this command does"
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional timeout in milliseconds (max 600000ms / 10 minutes). Defaults to 120000ms (2 minutes)."
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Set to true to run this command in the background. Returns immediately with a task_id."
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Reads a file from the local filesystem. Returns content with line numbers. Supports pagination for large files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read"
                },
                "offset": {
                    "type": "number",
                    "description": "The line number to start reading from (for large files)"
                },
                "limit": {
                    "type": "number",
                    "description": "The number of lines to read (for large files)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file (creates new file or overwrites existing)",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Performs exact string replacements in files. The edit will FAIL if old_string is not unique. Use replace_all to change every instance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to edit"
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact text to replace (must be unique in file)"
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with (must be different from old_string)"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences of old_string (default false)"
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }
    },
    {
        "name": "glob",
        "description": "Find files matching a glob pattern (e.g., '**/*.py', 'src/**/*.js')",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files against"
                },
                "path": {
                    "type": "string",
                    "description": "The directory to search in (defaults to current directory)"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "grep",
        "description": "A powerful search tool built on regex. Supports full regex syntax, file filtering, and multiple output modes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The regular expression pattern to search for in file contents"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in (defaults to current directory)"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.py', '*.{ts,tsx}')"
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search (default false)"
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "Output mode: 'content' shows matching lines, 'files_with_matches' shows file paths, 'count' shows match counts. Defaults to 'files_with_matches'."
                },
                "context": {
                    "type": "number",
                    "description": "Number of lines to show before and after each match (requires output_mode: 'content')"
                },
                "after_context": {
                    "type": "number",
                    "description": "Number of lines to show after each match (requires output_mode: 'content')"
                },
                "before_context": {
                    "type": "number",
                    "description": "Number of lines to show before each match (requires output_mode: 'content')"
                },
                "multiline": {
                    "type": "boolean",
                    "description": "Enable multiline mode where patterns can span lines (default false)"
                },
                "head_limit": {
                    "type": "number",
                    "description": "Limit output to first N results (default 100)"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files and directories in a given path",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to list"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "web_fetch",
        "description": "Fetch content from a URL and extract text",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch content from"
                },
                "prompt": {
                    "type": "string",
                    "description": "What information to extract from the page"
                }
            },
            "required": ["url", "prompt"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "ask_user_question",
        "description": "Ask the user questions during execution to gather preferences, clarify requirements, or get decisions on implementation choices. Use this when you need user input to proceed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "description": "Questions to ask the user (1-4 questions)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The complete question to ask the user"
                            },
                            "header": {
                                "type": "string",
                                "description": "Very short label displayed as a chip/tag (max 12 chars)"
                            },
                            "options": {
                                "type": "array",
                                "description": "The available choices for this question (2-4 options)",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {
                                            "type": "string",
                                            "description": "The display text for this option"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Explanation of what this option means"
                                        }
                                    },
                                    "required": ["label", "description"]
                                }
                            },
                            "multiSelect": {
                                "type": "boolean",
                                "description": "Set to true to allow multiple options to be selected"
                            }
                        },
                        "required": ["question", "header", "options", "multiSelect"]
                    }
                }
            },
            "required": ["questions"]
        }
    }
]

def execute_bash(command, description=None, timeout=None, run_in_background=False):
    """执行 bash 命令"""
    try:
        # 默认超时 2 分钟，最大 10 分钟
        timeout_seconds = min((timeout or 120000) / 1000, 600)

        if run_in_background:
            # 后台执行
            import threading
            import uuid
            task_id = str(uuid.uuid4())

            def run_command():
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        cwd='/root/claude-web'
                    )
                    # 保存结果到文件
                    output_file = f"/tmp/task_{task_id}.output"
                    with open(output_file, 'w') as f:
                        f.write(result.stdout)
                        if result.stderr:
                            f.write(f"\nSTDERR:\n{result.stderr}")
                except Exception as e:
                    output_file = f"/tmp/task_{task_id}.output"
                    with open(output_file, 'w') as f:
                        f.write(f"Error: {str(e)}")

            thread = threading.Thread(target=run_command)
            thread.start()

            return {
                "success": True,
                "task_id": task_id,
                "message": f"Command started in background. Use task_id to check status.",
                "output_file": f"/tmp/task_{task_id}.output"
            }

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd='/root/claude-web'
        )

        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"

        return {
            "success": True,
            "output": output or "Command executed successfully (no output)",
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout_seconds} seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_read_file(file_path, offset=None, limit=None):
    """读取文件内容"""
    try:
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        if os.path.isdir(abs_path):
            return {"success": False, "error": f"Path is a directory: {file_path}"}

        # 检查文件大小
        file_size = os.path.getsize(abs_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            return {"success": False, "error": f"File too large: {file_size} bytes. Use offset and limit parameters."}

        with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 添加行号
        lines = content.split('\n')

        # 应用分页
        if offset is not None or limit is not None:
            start = offset if offset is not None else 0
            end = start + limit if limit is not None else len(lines)
            lines = lines[start:end]
            line_start = start + 1
        else:
            line_start = 1
            # 默认限制为 2000 行
            if len(lines) > 2000:
                lines = lines[:2000]

        numbered_content = '\n'.join([f"{i+line_start:5d}→{line}" for i, line in enumerate(lines)])

        result = {
            "success": True,
            "content": numbered_content,
            "path": abs_path,
            "size": file_size,
            "total_lines": len(content.split('\n'))
        }

        if offset is not None or limit is not None:
            result["offset"] = offset or 0
            result["limit"] = limit or len(lines)

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_write_file(file_path, content):
    """写入文件"""
    try:
        abs_path = os.path.abspath(file_path)

        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "success": True,
            "message": f"File written successfully: {abs_path}",
            "path": abs_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_edit_file(file_path, old_string, new_string, replace_all=False):
    """编辑文件"""
    try:
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        if old_string == new_string:
            return {"success": False, "error": "old_string and new_string must be different"}

        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_string not in content:
            return {"success": False, "error": "old_string not found in file"}

        # 检查是否唯一
        count = content.count(old_string)
        if count > 1 and not replace_all:
            return {"success": False, "error": f"old_string appears {count} times in file. Use replace_all=true to replace all occurrences, or provide a more specific string."}

        new_content = content.replace(old_string, new_string)

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {
            "success": True,
            "message": f"File edited successfully: {abs_path}",
            "replacements": count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_glob(pattern, path=None):
    """查找匹配的文件"""
    try:
        search_path = path or '/root/claude-web'
        abs_path = os.path.abspath(search_path)

        # 切换到搜索目录
        original_dir = os.getcwd()
        os.chdir(abs_path)

        matches = glob_module.glob(pattern, recursive=True)
        matches = sorted(matches)[:100]  # 限制结果数量

        os.chdir(original_dir)

        if not matches:
            return {"success": True, "matches": [], "message": "No files found"}

        return {
            "success": True,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_grep(pattern, path=None, file_pattern=None, case_insensitive=False, output_mode='files_with_matches', context=None, after_context=None, before_context=None, multiline=False, head_limit=100):
    """搜索文件内容"""
    try:
        search_path = path or '/root/claude-web'
        abs_path = os.path.abspath(search_path)

        results = []
        files_with_matches = set()
        file_match_counts = {}

        # 编译正则表达式
        flags = re.IGNORECASE if case_insensitive else 0
        if multiline:
            flags |= re.MULTILINE | re.DOTALL
        regex = re.compile(pattern, flags)

        if os.path.isfile(abs_path):
            files_to_search = [abs_path]
        else:
            # 搜索目录
            if file_pattern:
                files_to_search = glob_module.glob(os.path.join(abs_path, '**', file_pattern), recursive=True)
            else:
                files_to_search = glob_module.glob(os.path.join(abs_path, '**', '*'), recursive=True)

            files_to_search = [f for f in files_to_search if os.path.isfile(f)][:200]  # 限制文件数

        for file_path in files_to_search:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if multiline:
                        content = f.read()
                        matches = list(regex.finditer(content))
                        if matches:
                            files_with_matches.add(file_path)
                            file_match_counts[file_path] = len(matches)
                            if output_mode == 'content':
                                for match in matches[:head_limit]:
                                    results.append({
                                        "file": file_path,
                                        "content": match.group(0)
                                    })
                    else:
                        lines = f.readlines()

                match_count = 0
                if not multiline:
                    for line_num, line in enumerate(lines, 1):
                        if regex.search(line):
                            match_count += 1
                            files_with_matches.add(file_path)

                            if output_mode == 'content':
                                # 计算上下文范围
                                before = before_context if before_context is not None else (context if context else 0)
                                after = after_context if after_context is not None else (context if context else 0)

                                # 添加上下文行
                                context_lines = []
                                if before or after:
                                    start = max(0, line_num - 1 - before)
                                    end = min(len(lines), line_num + after)
                                    for i in range(start, end):
                                        prefix = ">" if i == line_num - 1 else " "
                                        context_lines.append(f"{prefix} {i+1:5d}: {lines[i].rstrip()}")
                                    results.append({
                                        "file": file_path,
                                        "line": line_num,
                                        "content": '\n'.join(context_lines)
                                    })
                                else:
                                    results.append({
                                        "file": file_path,
                                        "line": line_num,
                                        "content": line.rstrip()
                                    })

                                if len(results) >= head_limit:
                                    break

                    if match_count > 0:
                        file_match_counts[file_path] = match_count

            except:
                continue

            if output_mode == 'content' and len(results) >= head_limit:
                break

        # 根据输出模式返回结果
        if output_mode == 'files_with_matches':
            return {
                "success": True,
                "files": sorted(list(files_with_matches))[:head_limit],
                "count": len(files_with_matches)
            }
        elif output_mode == 'count':
            count_results = [{"file": f, "matches": c} for f, c in sorted(file_match_counts.items())]
            return {
                "success": True,
                "results": count_results[:head_limit],
                "total_files": len(count_results)
            }
        else:  # content
            return {
                "success": True,
                "results": results[:head_limit],
                "count": len(results)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_list_directory(path):
    """列出目录内容"""
    try:
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"Path not found: {path}"}

        if not os.path.isdir(abs_path):
            return {"success": False, "error": f"Path is not a directory: {path}"}

        items = []
        for item in sorted(os.listdir(abs_path)):
            item_path = os.path.join(abs_path, item)
            is_dir = os.path.isdir(item_path)

            items.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "size": 0 if is_dir else os.path.getsize(item_path)
            })

        return {
            "success": True,
            "path": abs_path,
            "items": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_web_fetch(url, prompt):
    """获取网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 解析 HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        # 获取文本
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # 限制长度
        if len(text) > 5000:
            text = text[:5000] + "\n\n[内容已截断...]"

        return {
            "success": True,
            "url": url,
            "content": text,
            "prompt": prompt
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_web_search(query):
    """网页搜索（简化版，实际应使用搜索 API）"""
    try:
        # 这里使用 DuckDuckGo 的简单搜索
        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        results = []
        for result in soup.find_all('div', class_='result')[:5]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')

            if title_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'url': title_elem.get('href', ''),
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                })

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_ask_user_question(questions):
    """向用户提问（需要前端交互）"""
    # 这个工具需要特殊处理，返回一个标记让前端知道需要显示问题
    return {
        "success": True,
        "requires_user_input": True,
        "questions": questions
    }

def execute_tool(tool_name, tool_input):
    """执行工具调用"""
    if tool_name == "bash":
        return execute_bash(
            tool_input.get("command"),
            tool_input.get("description"),
            tool_input.get("timeout"),
            tool_input.get("run_in_background", False)
        )
    elif tool_name == "read_file":
        return execute_read_file(
            tool_input.get("file_path"),
            tool_input.get("offset"),
            tool_input.get("limit")
        )
    elif tool_name == "write_file":
        return execute_write_file(tool_input.get("file_path"), tool_input.get("content"))
    elif tool_name == "edit_file":
        return execute_edit_file(
            tool_input.get("file_path"),
            tool_input.get("old_string"),
            tool_input.get("new_string"),
            tool_input.get("replace_all", False)
        )
    elif tool_name == "glob":
        return execute_glob(tool_input.get("pattern"), tool_input.get("path"))
    elif tool_name == "grep":
        return execute_grep(
            tool_input.get("pattern"),
            tool_input.get("path"),
            tool_input.get("file_pattern"),
            tool_input.get("case_insensitive", False),
            tool_input.get("output_mode", 'files_with_matches'),
            tool_input.get("context"),
            tool_input.get("after_context"),
            tool_input.get("before_context"),
            tool_input.get("multiline", False),
            tool_input.get("head_limit", 100)
        )
    elif tool_name == "list_directory":
        return execute_list_directory(tool_input.get("path"))
    elif tool_name == "web_fetch":
        return execute_web_fetch(tool_input.get("url"), tool_input.get("prompt"))
    elif tool_name == "web_search":
        return execute_web_search(tool_input.get("query"))
    elif tool_name == "ask_user_question":
        return execute_ask_user_question(tool_input.get("questions"))
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

# 工具元数据 - 用于权限检查
TOOL_METADATA = {
    "bash": {
        "requires_permission": True,
        "description": "执行bash命令可能会修改系统状态"
    },
    "write_file": {
        "requires_permission": True,
        "description": "写入文件会修改文件系统"
    },
    "edit_file": {
        "requires_permission": True,
        "description": "编辑文件会修改文件内容"
    },
    "read_file": {
        "requires_permission": False,
        "description": "只读操作，无需权限"
    },
    "glob": {
        "requires_permission": False,
        "description": "只读操作，无需权限"
    },
    "grep": {
        "requires_permission": False,
        "description": "只读操作，无需权限"
    },
    "list_directory": {
        "requires_permission": False,
        "description": "只读操作，无需权限"
    },
    "web_fetch": {
        "requires_permission": False,
        "description": "只读操作，无需权限"
    },
    "web_search": {
        "requires_permission": False,
        "description": "只读操作，无需权限"
    }
}
