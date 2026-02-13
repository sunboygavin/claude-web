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
from mcp.security import init_encryption
from mcp.manager import get_mcp_manager
from tool_router import get_tool_router
from operation_logger import (
    get_operation_logs,
    get_pending_operations,
    grant_permission,
    reject_permission,
    get_operation_stats
)
import mcp_database

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 使用配置文件中的设置
ANTHROPIC_BASE_URL = config.ANTHROPIC_BASE_URL
ANTHROPIC_AUTH_TOKEN = config.ANTHROPIC_AUTH_TOKEN

# 初始化MCP
init_encryption(config.SECRET_KEY)
mcp_manager = get_mcp_manager()
tool_router = get_tool_router()

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

@app.route('/api/save-message', methods=['POST'])
@login_required
def save_message_api():
    """保存消息到数据库"""
    try:
        data = request.json
        username = session.get('username')
        current_model = session.get('model', config.DEFAULT_MODEL)
        session_id = session.get('session_id')

        role = data.get('role')
        content = data.get('content')
        metadata = data.get('metadata')

        database.save_message(username, role, content, current_model, session_id, metadata)

        return jsonify({'success': True})
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
                # 获取所有工具（包括MCP工具）
                all_tools = tool_router.get_all_tools()

                # Agentic loop - 持续执行直到Claude不再调用工具
                max_iterations = 25  # 防止无限循环
                iteration = 0

                while iteration < max_iterations:
                    iteration += 1

                    # 调用Claude API
                    response = client.messages.create(
                        model=model_id,
                        max_tokens=4096,
                        messages=messages,
                        tools=all_tools,
                        system=system_prompt.get_system_prompt(),
                        stream=True
                    )

                    current_text = ""
                    tool_uses = []
                    has_tool_use = False

                        for event in response:
                        if event.type == "content_block_start":
                            if hasattr(event.content_block, 'type'):
                                if event.content_block.type == "tool_use":
                                    has_tool_use = True
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

                    # 如果没有工具调用，说明对话结束
                    if not has_tool_use:
                        break

                    # 处理所有工具调用
                    tool_results = []
                    for tool_use in tool_uses:
                        if "input_json" not in tool_use:
                            continue

                        tool_input = json.loads(tool_use["input_json"])
                        tool_name = tool_use["name"]

                        # 发送工具调用信息
                        yield f"data: {json.dumps({'type': 'tool_use', 'name': tool_name, 'input': tool_input})}\n\n"

                        # 执行工具
                        exec_result = tool_router.execute_tool(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            username=username,
                            session_id=session_id,
                            auto_approve=False
                        )

                        # 检查是否需要用户输入
                        if exec_result.get('status') == 'success' and exec_result.get('result', {}).get('requires_user_input'):
                            yield f"data: {json.dumps({'type': 'waiting_user_input'})}\n\n"
                            if assistant_response:
                                database.save_message(username, 'assistant', assistant_response, current_model, session_id)
                            return

                        # 检查是否需要权限
                        if exec_result['status'] == 'pending_permission':
                            yield f"data: {json.dumps({'type': 'permission_required', 'log_id': exec_result['log_id'], 'preview': exec_result['preview']})}\n\n"
                            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                            if assistant_response:
                                database.save_message(username, 'assistant', assistant_response, current_model, session_id)
                            return

                        # 获取执行结果
                        if exec_result['status'] == 'success':
                            result = exec_result['result']
                        else:
                            result = {'error': exec_result.get('error', '执行失败')}

                        # 发送工具结果
                        yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_name, 'result': result})}\n\n"

                        # 保存工具结果用于下一轮
                        tool_results.append({
                            "tool_use": tool_use,
                            "result": result
                        })

                    # 构建下一轮消息
                    # 添加assistant的响应（包含文本和工具调用）
                    assistant_content = []
                    if current_text:
                        assistant_content.append({"type": "text", "text": current_text})
                    for tr in tool_results:
                        assistant_content.append({
                            "type": "tool_use",
                            "id": tr["tool_use"]["id"],
                            "name": tr["tool_use"]["name"],
                            "input": json.loads(tr["tool_use"]["input_json"])
                        })
                    messages.append({"role": "assistant", "content": assistant_content})

                    # 添加工具结果
                    tool_result_content = []
                    for tr in tool_results:
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": tr["tool_use"]["id"],
                            "content": json.dumps(tr["result"])
                        })
                    messages.append({"role": "user", "content": tool_result_content})

                    # 重置状态，继续下一轮
                    current_text = ""
                    tool_uses = []

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

# MCP Configuration Endpoints

@app.route('/mcp-config')
@login_required
def mcp_config():
    """MCP配置页面"""
    return render_template('mcp_config.html')

@app.route('/api/mcp/servers', methods=['GET', 'POST'])
@login_required
def mcp_servers():
    """获取或添加MCP服务器"""
    try:
        if request.method == 'GET':
            servers = mcp_database.get_mcp_servers(enabled_only=False)
            # 获取每个服务器的状态
            for server in servers:
                status = mcp_database.get_server_status(server['id'])
                server['status'] = status if status else {'status': 'unknown'}
            return jsonify({'success': True, 'servers': servers})

        elif request.method == 'POST':
            data = request.json
            server_id = mcp_database.add_mcp_server(
                name=data['name'],
                server_type=data['server_type'],
                command=data.get('command'),
                args=data.get('args'),
                env=data.get('env'),
                url=data.get('url'),
                config=data.get('config')
            )
            return jsonify({'success': True, 'server_id': server_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/servers/<int:server_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def mcp_server_detail(server_id):
    """获取、更新或删除MCP服务器"""
    try:
        if request.method == 'GET':
            server = mcp_database.get_mcp_server(server_id)
            if not server:
                return jsonify({'error': '服务器未找到'}), 404
            status = mcp_database.get_server_status(server_id)
            server['status'] = status if status else {'status': 'unknown'}
            return jsonify({'success': True, 'server': server})

        elif request.method == 'PUT':
            data = request.json
            success = mcp_database.update_mcp_server(server_id, **data)
            if success:
                return jsonify({'success': True})
            return jsonify({'error': '更新失败'}), 500

        elif request.method == 'DELETE':
            success = mcp_database.delete_mcp_server(server_id)
            if success:
                return jsonify({'success': True})
            return jsonify({'error': '删除失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/servers/<int:server_id>/credentials', methods=['POST'])
@login_required
def mcp_server_credentials(server_id):
    """添加或更新服务器凭证"""
    try:
        data = request.json
        credential_id = mcp_database.save_credential(
            server_id=server_id,
            credential_type=data['credential_type'],
            credential_key=data['credential_key'],
            credential_value=data['credential_value']
        )
        return jsonify({'success': True, 'credential_id': credential_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/servers/<int:server_id>/status', methods=['GET'])
@login_required
def mcp_server_status(server_id):
    """获取服务器状态"""
    try:
        status = mcp_database.get_server_status(server_id)
        if status:
            return jsonify({'success': True, 'status': status})
        return jsonify({'success': True, 'status': {'status': 'unknown'}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/servers/<int:server_id>/test', methods=['POST'])
@login_required
def mcp_server_test(server_id):
    """测试服务器连接"""
    try:
        # 尝试重启服务器来测试连接
        success = mcp_manager.restart_server(server_id)
        if success:
            return jsonify({'success': True, 'message': '连接成功'})
        return jsonify({'success': False, 'message': '连接失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/servers/<int:server_id>/restart', methods=['POST'])
@login_required
def mcp_server_restart(server_id):
    """重启服务器"""
    try:
        success = mcp_manager.restart_server(server_id)
        if success:
            return jsonify({'success': True, 'message': '服务器已重启'})
        return jsonify({'success': False, 'message': '重启失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Operation Log Endpoints

@app.route('/api/operations/logs', methods=['GET'])
@login_required
def operations_logs():
    """获取操作日志"""
    try:
        username = session.get('username')
        session_id = session.get('session_id')
        status = request.args.get('status')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        logs = get_operation_logs(
            username=username,
            session_id=session_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return jsonify({'success': True, 'logs': logs})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/operations/pending', methods=['GET'])
@login_required
def operations_pending():
    """获取待审批操作"""
    try:
        username = session.get('username')
        session_id = session.get('session_id')

        pending = get_pending_operations(username=username, session_id=session_id)

        return jsonify({'success': True, 'pending': pending})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/operations/<int:log_id>/approve', methods=['POST'])
@login_required
def operations_approve(log_id):
    """批准操作"""
    try:
        grant_permission(log_id)

        # 执行已批准的操作
        result = tool_router.execute_approved_operation(log_id)

        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/operations/<int:log_id>/reject', methods=['POST'])
@login_required
def operations_reject(log_id):
    """拒绝操作"""
    try:
        data = request.json
        reason = data.get('reason', '用户拒绝')

        reject_permission(log_id, reason)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/operations/stats', methods=['GET'])
@login_required
def operations_stats():
    """获取操作统计"""
    try:
        username = session.get('username')
        session_id = session.get('session_id')

        stats = get_operation_stats(username=username, session_id=session_id)

        return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/operations/stream')
@login_required
def operations_stream():
    """SSE流式推送操作日志"""
    def generate():
        username = session.get('username')
        session_id = session.get('session_id')

        # 发送初始数据
        logs = get_operation_logs(username=username, session_id=session_id, limit=10)
        yield f"data: {json.dumps({'type': 'initial', 'logs': logs})}\n\n"

        # 保持连接并定期发送更新
        import time
        while True:
            time.sleep(2)  # 每2秒检查一次
            logs = get_operation_logs(username=username, session_id=session_id, limit=10)
            yield f"data: {json.dumps({'type': 'update', 'logs': logs})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # 启动时初始化MCP服务器
    try:
        mcp_manager.start_all_servers()
    except Exception as e:
        print(f"Warning: Failed to start MCP servers: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)
