from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
import anthropic
import os
from datetime import datetime
from functools import wraps
import config
import tools
import json
import database
import uuid
import system_prompt

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 使用配置文件中的设置
ANTHROPIC_BASE_URL = config.ANTHROPIC_BASE_URL
ANTHROPIC_AUTH_TOKEN = config.ANTHROPIC_AUTH_TOKEN

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')

        if username in config.USERS and config.USERS[username] == password:
            session['username'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # 初始化会话模型
    if 'model' not in session:
        session['model'] = config.DEFAULT_MODEL
    # 初始化会话 ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html', current_model=session.get('model', 'sonnet'))

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    """列出指定目录下的文件和文件夹"""
    try:
        path = request.args.get('path', '/root/claude-web')

        # 安全检查：确保路径在项目目录内
        abs_path = os.path.abspath(path)
        base_path = os.path.abspath('/root/claude-web')
        if not abs_path.startswith(base_path):
            return jsonify({'error': '无权访问此路径'}), 403

        if not os.path.exists(abs_path):
            return jsonify({'error': '路径不存在'}), 404

        items = []
        for item in sorted(os.listdir(abs_path)):
            item_path = os.path.join(abs_path, item)
            is_dir = os.path.isdir(item_path)

            # 跳过隐藏文件和特殊目录
            if item.startswith('.') and item not in ['.gitignore', '.env.example']:
                continue

            items.append({
                'name': item,
                'path': item_path,
                'is_dir': is_dir,
                'size': os.path.getsize(item_path) if not is_dir else 0
            })

        return jsonify({
            'current_path': abs_path,
            'items': items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file', methods=['GET', 'POST'])
@login_required
def file_operations():
    """读取或保存文件内容"""
    try:
        if request.method == 'GET':
            file_path = request.args.get('path', '')

            # 安全检查
            abs_path = os.path.abspath(file_path)
            base_path = os.path.abspath('/root/claude-web')
            if not abs_path.startswith(base_path):
                return jsonify({'error': '无权访问此文件'}), 403

            if not os.path.exists(abs_path) or os.path.isdir(abs_path):
                return jsonify({'error': '文件不存在'}), 404

            # 检查文件扩展名
            _, ext = os.path.splitext(abs_path)
            if ext not in config.ALLOWED_EXTENSIONS:
                return jsonify({'error': '不支持的文件类型'}), 400

            # 检查文件大小
            if os.path.getsize(abs_path) > config.MAX_FILE_SIZE:
                return jsonify({'error': '文件过大'}), 400

            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return jsonify({
                'path': abs_path,
                'content': content
            })

        elif request.method == 'POST':
            data = request.json
            file_path = data.get('path', '')
            content = data.get('content', '')

            # 安全检查
            abs_path = os.path.abspath(file_path)
            base_path = os.path.abspath('/root/claude-web')
            if not abs_path.startswith(base_path):
                return jsonify({'error': '无权访问此文件'}), 403

            # 检查文件扩展名
            _, ext = os.path.splitext(abs_path)
            if ext not in config.ALLOWED_EXTENSIONS:
                return jsonify({'error': '不支持的文件类型'}), 400

            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return jsonify({'success': True, 'message': '文件保存成功'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/model', methods=['GET', 'POST'])
@login_required
def model_operations():
    """获取或设置当前模型"""
    try:
        if request.method == 'GET':
            current_model = session.get('model', config.DEFAULT_MODEL)
            return jsonify({
                'current_model': current_model,
                'available_models': list(config.AVAILABLE_MODELS.keys()),
                'model_info': {
                    'sonnet': 'Claude Sonnet 4.5 - 平衡性能和速度',
                    'opus': 'Claude Opus 4.6 - 最强大的模型',
                    'haiku': 'Claude Haiku 3.5 - 最快速的模型'
                }
            })
        elif request.method == 'POST':
            data = request.json
            model = data.get('model', '').lower()

            if model not in config.AVAILABLE_MODELS:
                return jsonify({'error': f'无效的模型: {model}'}), 400

            session['model'] = model
            return jsonify({
                'success': True,
                'model': model,
                'message': f'已切换到 {model.upper()} 模型'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
@login_required
def clear_history():
    """清除对话历史"""
    username = session.get('username')
    deleted_count = database.clear_user_history(username)
    # 生成新的会话 ID
    session['session_id'] = str(uuid.uuid4())
    return jsonify({'success': True, 'message': f'已清除 {deleted_count} 条对话历史'})

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """获取对话历史"""
    username = session.get('username')
    limit = request.args.get('limit', 100, type=int)
    history = database.get_conversation_history(username, limit)
    return jsonify({'success': True, 'history': history})

@app.route('/api/search', methods=['POST'])
@login_required
def search_history():
    """搜索对话历史"""
    username = session.get('username')
    data = request.json
    query = data.get('query', '')
    limit = data.get('limit', 50)

    if not query:
        return jsonify({'error': '搜索关键词不能为空'}), 400

    results = database.search_conversations(username, query, limit)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """获取对话统计信息"""
    username = session.get('username')
    stats = database.get_conversation_stats(username)
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/export', methods=['POST'])
@login_required
def export_conversation():
    """导出对话历史"""
    try:
        data = request.json
        history = data.get('history', [])

        # 生成导出内容
        export_text = "# Claude 对话导出\n\n"
        export_text += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += f"模型: {session.get('model', 'sonnet').upper()}\n\n"
        export_text += "---\n\n"

        for msg in history:
            role = "用户" if msg['role'] == 'user' else "Claude"
            export_text += f"## {role}\n\n{msg['content']}\n\n"

        return jsonify({
            'success': True,
            'content': export_text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        username = session.get('username')
        current_model = session.get('model', config.DEFAULT_MODEL)
        session_id = session.get('session_id')

        if not ANTHROPIC_AUTH_TOKEN:
            return jsonify({'error': 'API Token 未设置'}), 500

        # 保存用户消息到数据库
        database.save_message(username, 'user', user_message, current_model, session_id)

        # 处理命令
        if user_message.startswith('/'):
            command_result = handle_command(user_message)
            if command_result:
                return jsonify(command_result)

        # 获取当前模型
        current_model = session.get('model', config.DEFAULT_MODEL)
        model_id = config.AVAILABLE_MODELS.get(current_model, config.AVAILABLE_MODELS['sonnet'])

        client = anthropic.Anthropic(
            api_key=ANTHROPIC_AUTH_TOKEN,
            base_url=ANTHROPIC_BASE_URL
        )

        # 构建消息历史
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        def generate():
            assistant_response = ""
            try:
                # 使用工具调用
                response = client.messages.create(
                    model=model_id,
                    max_tokens=4096,
                    messages=messages,
                    tools=tools.TOOLS,
                    system=system_prompt.get_system_prompt(),
                    stream=True
                )

                current_text = ""
                tool_uses = []

                for event in response:
                    if event.type == "content_block_start":
                        if hasattr(event.content_block, 'type'):
                            if event.content_block.type == "tool_use":
                                tool_uses.append({
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": {}
                                })

                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, 'type'):
                            if event.delta.type == "text_delta":
                                text = event.delta.text
                                current_text += text
                                assistant_response += text
                                yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
                            elif event.delta.type == "input_json_delta":
                                if tool_uses:
                                    tool_uses[-1]["input_json"] = tool_uses[-1].get("input_json", "") + event.delta.partial_json

                    elif event.type == "content_block_stop":
                        # 工具调用完成，执行工具
                        if tool_uses:
                            for tool_use in tool_uses:
                                if "input_json" in tool_use:
                                    tool_input = json.loads(tool_use["input_json"])
                                    tool_name = tool_use["name"]

                                    # 发送工具调用信息
                                    yield f"data: {json.dumps({'type': 'tool_use', 'name': tool_name, 'input': tool_input})}\n\n"

                                    # 执行工具
                                    result = tools.execute_tool(tool_name, tool_input)

                                    # 发送工具结果
                                    yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_name, 'result': result})}\n\n"

                                    # 继续对话，将工具结果发送给 Claude
                                    messages.append({
                                        "role": "assistant",
                                        "content": [
                                            {"type": "text", "text": current_text} if current_text else None,
                                            {
                                                "type": "tool_use",
                                                "id": tool_use["id"],
                                                "name": tool_name,
                                                "input": tool_input
                                            }
                                        ]
                                    })
                                    messages[-1]["content"] = [c for c in messages[-1]["content"] if c]

                                    messages.append({
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_use["id"],
                                                "content": json.dumps(result)
                                            }
                                        ]
                                    })

                                    # 继续流式响应
                                    follow_up = client.messages.create(
                                        model=model_id,
                                        max_tokens=4096,
                                        messages=messages,
                                        tools=tools.TOOLS,
                                        system=system_prompt.get_system_prompt(),
                                        stream=True
                                    )

                                    for follow_event in follow_up:
                                        if follow_event.type == "content_block_delta":
                                            if hasattr(follow_event.delta, 'type') and follow_event.delta.type == "text_delta":
                                                assistant_response += follow_event.delta.text
                                                yield f"data: {json.dumps({'type': 'text', 'content': follow_event.delta.text})}\n\n"

                # 保存 assistant 响应到数据库
                if assistant_response:
                    database.save_message(username, 'assistant', assistant_response, current_model, session_id)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_command(command):
    """处理命令"""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''

    if cmd == '/help':
        help_text = """
# Claude Code 网页版 - 帮助

## 可用命令：

- **/help** - 显示此帮助信息
- **/model [sonnet|opus|haiku]** - 切换模型或查看当前模型
- **/clear** - 清除对话历史
- **/export** - 导出对话历史
- **/tools** - 查看可用工具列表

## 可用工具：

1. **bash** - 执行 bash 命令
2. **read_file** - 读取文件内容
3. **write_file** - 创建或覆盖文件
4. **edit_file** - 编辑文件（字符串替换）
5. **glob** - 文件模式匹配搜索
6. **grep** - 正则表达式内容搜索
7. **list_directory** - 列出目录内容

## 使用提示：

- 你可以直接向 Claude 提问或请求帮助
- Claude 可以自动调用工具来完成任务
- 点击左侧文件浏览器可以查看和编辑文件
- 使用 /model 命令切换不同的 Claude 模型
"""
        return {'type': 'command', 'content': help_text}

    elif cmd == '/model':
        if args:
            model = args.lower()
            if model in config.AVAILABLE_MODELS:
                session['model'] = model
                return {'type': 'command', 'content': f'✓ 已切换到 {model.upper()} 模型'}
            else:
                return {'type': 'command', 'content': f'✗ 无效的模型: {model}\n可用模型: sonnet, opus, haiku'}
        else:
            current = session.get('model', config.DEFAULT_MODEL)
            return {'type': 'command', 'content': f'当前模型: {current.upper()}\n可用模型: sonnet, opus, haiku'}

    elif cmd == '/clear':
        return {'type': 'command', 'content': '✓ 对话历史已清除', 'clear': True}

    elif cmd == '/export':
        return {'type': 'command', 'content': '请使用界面上的导出按钮导出对话历史'}

    elif cmd == '/tools':
        tools_text = """
# 可用工具列表

1. **bash** - 执行 bash 命令
   - 用于 git、npm、docker 等终端操作

2. **read_file** - 读取文件内容
   - 支持带行号的文件显示

3. **write_file** - 创建或覆盖文件
   - 自动创建目录

4. **edit_file** - 编辑文件
   - 通过字符串替换修改文件

5. **glob** - 文件模式匹配
   - 支持 **/*.py 等模式

6. **grep** - 内容搜索
   - 支持正则表达式搜索

7. **list_directory** - 列出目录
   - 显示文件和文件夹信息
"""
        return {'type': 'command', 'content': tools_text}

    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
