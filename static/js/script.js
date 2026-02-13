let conversationHistory = [];
let isProcessing = false;
let currentFilePath = null;
let currentModel = 'sonnet';

const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const sidebar = document.getElementById('sidebar');
const fileTree = document.getElementById('fileTree');
const editorContainer = document.getElementById('editorContainer');
const chatSection = document.getElementById('chatSection');
const codeEditor = document.getElementById('codeEditor');
const currentFilePathSpan = document.getElementById('currentFilePath');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadFileTree('/root/claude-web');
    loadCurrentModel();
    loadHistoryFromDB();

    // 侧边栏切换
    document.getElementById('toggleSidebar').addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // 关闭编辑器
    document.getElementById('closeEditorBtn').addEventListener('click', () => {
        editorContainer.style.display = 'none';
        chatSection.style.display = 'flex';
        currentFilePath = null;
    });

    // 保存文件
    document.getElementById('saveFileBtn').addEventListener('click', saveFile);

    // 清除历史
    document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);

    // 导出对话
    document.getElementById('exportBtn').addEventListener('click', exportConversation);

    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', openSearchModal);

    // 历史按钮
    document.getElementById('historyBtn').addEventListener('click', openHistoryModal);

    // 操作日志按钮
    document.getElementById('operationsBtn').addEventListener('click', openOperationsModal);

    // 模型选择
    document.getElementById('modelSelector').addEventListener('change', changeModel);
});

// 加载文件树
async function loadFileTree(path) {
    try {
        const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (!response.ok) {
            fileTree.innerHTML = `<div class="loading">错误: ${data.error}</div>`;
            return;
        }

        fileTree.innerHTML = '';

        // 添加返回上级目录按钮
        if (path !== '/root/claude-web') {
            const backItem = document.createElement('div');
            backItem.className = 'folder-item';
            backItem.innerHTML = '<span class="folder-icon">📁</span><span>..</span>';
            backItem.onclick = () => {
                const parentPath = path.split('/').slice(0, -1).join('/');
                loadFileTree(parentPath || '/root/claude-web');
            };
            fileTree.appendChild(backItem);
        }

        // 显示文件夹
        data.items.filter(item => item.is_dir).forEach(item => {
            const folderItem = document.createElement('div');
            folderItem.className = 'folder-item';
            folderItem.innerHTML = `<span class="folder-icon">📁</span><span>${item.name}</span>`;
            folderItem.onclick = () => loadFileTree(item.path);
            fileTree.appendChild(folderItem);
        });

        // 显示文件
        data.items.filter(item => !item.is_dir).forEach(item => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `<span class="file-icon">📄</span><span>${item.name}</span>`;
            fileItem.onclick = () => openFile(item.path);
            fileTree.appendChild(fileItem);
        });

    } catch (error) {
        fileTree.innerHTML = `<div class="loading">加载失败: ${error.message}</div>`;
    }
}

// 打开文件
async function openFile(path) {
    try {
        const response = await fetch(`/api/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (!response.ok) {
            alert(`错误: ${data.error}`);
            return;
        }

        currentFilePath = data.path;
        currentFilePathSpan.textContent = data.path;
        codeEditor.value = data.content;

        chatSection.style.display = 'none';
        editorContainer.style.display = 'flex';

    } catch (error) {
        alert(`打开文件失败: ${error.message}`);
    }
}

// 保存文件
async function saveFile() {
    if (!currentFilePath) return;

    try {
        const response = await fetch('/api/file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentFilePath,
                content: codeEditor.value
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('文件保存成功！');
        } else {
            alert(`保存失败: ${data.error}`);
        }

    } catch (error) {
        alert(`保存失败: ${error.message}`);
    }
}

// 加载当前模型
async function loadCurrentModel() {
    try {
        const response = await fetch('/api/model');
        const data = await response.json();

        if (response.ok) {
            currentModel = data.current_model;
            const selector = document.getElementById('modelSelector');
            if (selector) {
                selector.value = currentModel;
            }
            updateModelDisplay();
        }
    } catch (error) {
        console.error('加载模型失败:', error);
    }
}

// 切换模型
async function changeModel(event) {
    const newModel = event.target.value;

    try {
        const response = await fetch('/api/model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: newModel })
        });

        const data = await response.json();

        if (response.ok) {
            currentModel = newModel;
            updateModelDisplay();
            addSystemMessage(`✓ 已切换到 ${newModel.toUpperCase()} 模型`);
        } else {
            alert(`切换模型失败: ${data.error}`);
            event.target.value = currentModel;
        }
    } catch (error) {
        alert(`切换模型失败: ${error.message}`);
        event.target.value = currentModel;
    }
}

// 更新模型显示
function updateModelDisplay() {
    const modelNames = {
        'sonnet': 'Claude Sonnet 4.5',
        'opus': 'Claude Opus 4.6',
        'haiku': 'Claude Haiku 3.5'
    };

    const modelInfo = document.querySelector('.model-info');
    if (modelInfo) {
        modelInfo.textContent = `Model: ${modelNames[currentModel] || currentModel}`;
    }
}

// 清除历史
async function clearHistory() {
    if (!confirm('确定要清除所有对话历史吗？')) {
        return;
    }

    try {
        const response = await fetch('/api/clear', {
            method: 'POST'
        });

        if (response.ok) {
            conversationHistory = [];
            chatContainer.innerHTML = '<div class="welcome-message"><h2>👋 你好！我是 Claude</h2><p>我可以帮助你解答问题、编写代码、分析文档等。请随时向我提问！</p></div>';
            addSystemMessage('✓ 对话历史已清除');
        }
    } catch (error) {
        alert(`清除失败: ${error.message}`);
    }
}

// 导出对话
async function exportConversation() {
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ history: conversationHistory })
        });

        const data = await response.json();

        if (response.ok) {
            // 创建下载链接
            const blob = new Blob([data.content], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `claude-conversation-${new Date().toISOString().slice(0, 10)}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            addSystemMessage('✓ 对话已导出');
        } else {
            alert(`导出失败: ${data.error}`);
        }
    } catch (error) {
        alert(`导出失败: ${error.message}`);
    }
}

// 添加系统消息
function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 滚动到底部
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 自动调整输入框高度
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// 回车发送消息
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function addMessage(role, content) {
    // 移除欢迎消息
    const welcomeMessage = chatContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);

    scrollToBottom();

    return contentDiv;
}

function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'typingIndicator';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(indicator);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

async function sendMessage() {
    if (isProcessing) return;

    const message = messageInput.value.trim();
    if (!message) return;

    isProcessing = true;
    sendButton.disabled = true;

    // 添加用户消息
    addMessage('user', message);
    conversationHistory.push({ role: 'user', content: message });

    messageInput.value = '';
    messageInput.style.height = 'auto';

    // 检查是否是命令
    if (message.startsWith('/')) {
        await handleCommand(message);
        isProcessing = false;
        sendButton.disabled = false;
        messageInput.focus();
        return;
    }

    // 显示输入指示器
    showTypingIndicator();

    try {
        // 获取auto_approve设置
        const autoApprove = document.getElementById('autoApproveToggle').checked;

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory.slice(0, -1),
                auto_approve: autoApprove
            })
        });

        removeTypingIndicator();

        if (!response.ok) {
            const error = await response.json();
            addMessage('assistant', `错误: ${error.error}`);
            isProcessing = false;
            sendButton.disabled = false;
            return;
        }

        // 创建助手消息容器
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        chatContainer.appendChild(messageDiv);

        let fullResponse = '';
        let currentTextDiv = null;
        let toolCalls = []; // 记录工具调用

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        console.log('Received SSE data:', data); // 调试日志

                        if (data.type === 'text') {
                            // 文本内容
                            if (!currentTextDiv) {
                                currentTextDiv = document.createElement('div');
                                currentTextDiv.className = 'message-content';
                                messageDiv.appendChild(currentTextDiv);
                            }
                            fullResponse += data.content;
                            currentTextDiv.textContent = fullResponse;
                            scrollToBottom();

                        } else if (data.type === 'tool_use') {
                            // 工具调用
                            const toolDiv = document.createElement('div');
                            toolDiv.className = 'tool-use';
                            toolDiv.innerHTML = `
                                <div class="tool-header">🔧 ${data.name}</div>
                                <pre class="tool-input">${JSON.stringify(data.input, null, 2)}</pre>
                            `;
                            messageDiv.appendChild(toolDiv);
                            scrollToBottom();

                            // 记录工具调用
                            toolCalls.push({
                                type: 'tool_use',
                                name: data.name,
                                input: data.input
                            });

                        } else if (data.type === 'tool_result') {
                            // 工具结果
                            console.log('Tool result received:', data);

                            // 检查是否是用户问题
                            if (data.result && data.result.requires_user_input && data.result.questions) {
                                // 显示用户问题界面
                                console.log('Showing user questions:', data.result.questions);
                                showUserQuestions(data.result.questions, messageDiv);
                                scrollToBottom();
                            } else {
                                // 正常的工具结果
                                const resultDiv = document.createElement('div');
                                resultDiv.className = 'tool-result';

                                let resultContent = '';
                                if (data.result && data.result.success) {
                                    resultContent = data.result.output || data.result.content || data.result.message || JSON.stringify(data.result, null, 2);
                                } else if (data.result) {
                                    resultContent = `❌ Error: ${data.result.error}`;
                                } else {
                                    resultContent = JSON.stringify(data.result, null, 2);
                                }

                                resultDiv.innerHTML = `
                                    <div class="tool-result-header">📋 Result</div>
                                    <pre class="tool-result-content">${resultContent}</pre>
                                `;
                                messageDiv.appendChild(resultDiv);
                                scrollToBottom();
                            }

                            // 记录工具结果
                            toolCalls.push({
                                type: 'tool_result',
                                name: data.name,
                                result: data.result
                            });

                            // 重置文本容器，为后续文本做准备
                            currentTextDiv = null;

                        } else if (data.type === 'permission_required') {
                            // 需要权限审批
                            console.log('Permission required:', data); // 调试日志

                            const permissionDiv = document.createElement('div');
                            permissionDiv.className = 'permission-request';
                            permissionDiv.id = `permission-${data.log_id}`;

                            // 转义HTML以防止XSS，但保留换行
                            const previewText = (data.preview || '此操作需要您的批准')
                                .replace(/&/g, '&amp;')
                                .replace(/</g, '&lt;')
                                .replace(/>/g, '&gt;')
                                .replace(/\n/g, '<br>');

                            permissionDiv.innerHTML = `
                                <div class="permission-header">⚠️ 需要权限审批</div>
                                <div class="permission-preview">${previewText}</div>
                                <div class="permission-actions">
                                    <button class="approve-btn" onclick="approvePermission(${data.log_id})">批准</button>
                                    <button class="reject-btn" onclick="rejectPermission(${data.log_id})">拒绝</button>
                                </div>
                            `;
                            messageDiv.appendChild(permissionDiv);
                            scrollToBottom();

                            // 确保权限请求可见
                            console.log('Permission div added to DOM:', permissionDiv);

                        } else if (data.type === 'waiting_user_input') {
                            // 等待用户输入（ask_user_question）
                            console.log('Waiting for user input');
                            // 显示提示信息
                            const waitingDiv = document.createElement('div');
                            waitingDiv.className = 'waiting-input';
                            waitingDiv.innerHTML = `
                                <div class="waiting-header">⏸️ 等待用户回答</div>
                                <div class="waiting-message">Claude正在等待您回答上面的问题</div>
                            `;
                            messageDiv.appendChild(waitingDiv);
                            scrollToBottom();

                        } else if (data.type === 'error') {
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'message-content error';
                            errorDiv.textContent = `错误: ${data.error}`;
                            messageDiv.appendChild(errorDiv);
                        }
                    } catch (e) {
                        // 忽略 JSON 解析错误
                    }
                }
            }
        }

        const assistantMessage = {
            role: 'assistant',
            content: fullResponse,
            html: messageDiv.innerHTML, // 保存完整HTML
            toolCalls: toolCalls // 保存工具调用信息
        };

        conversationHistory.push(assistantMessage);

        // 保存到数据库
        try {
            await fetch('/api/save-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    role: 'assistant',
                    content: fullResponse,
                    metadata: {
                        html: messageDiv.innerHTML,
                        toolCalls: toolCalls
                    }
                })
            });
        } catch (error) {
            console.error('保存消息失败:', error);
        }

    } catch (error) {
        removeTypingIndicator();
        addMessage('assistant', `错误: ${error.message}`);
    }

    isProcessing = false;
    sendButton.disabled = false;
    messageInput.focus();
}

// 处理命令
async function handleCommand(command) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: command,
                history: []
            })
        });

        if (!response.ok) {
            const error = await response.json();
            addMessage('assistant', `错误: ${error.error}`);
            return;
        }

        const data = await response.json();

        if (data.type === 'command') {
            // 渲染 Markdown 格式的命令响应
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content command-response';
            contentDiv.innerHTML = formatMarkdown(data.content);

            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            scrollToBottom();

            // 如果是清除命令，清空历史
            if (data.clear) {
                conversationHistory = [];
            }
        }
    } catch (error) {
        addMessage('assistant', `错误: ${error.message}`);
    }
}

// 简单的 Markdown 格式化
function formatMarkdown(text) {
    return text
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^\*\*(.+?)\*\*$/gm, '<strong>$1</strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

// 从数据库加载历史记录
async function loadHistoryFromDB() {
    try {
        const response = await fetch('/api/history?limit=50');
        const data = await response.json();

        if (response.ok && data.history && data.history.length > 0) {
            // 清空当前显示
            const welcomeMessage = chatContainer.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }

            // 显示历史消息
            data.history.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.role}`;

                // 如果有保存的HTML（包含工具调用），使用HTML
                if (msg.metadata && msg.metadata.html) {
                    messageDiv.innerHTML = msg.metadata.html;
                } else {
                    // 否则使用纯文本
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';
                    contentDiv.textContent = msg.content;
                    messageDiv.appendChild(contentDiv);
                }

                chatContainer.appendChild(messageDiv);

                // 添加到内存中的历史记录
                conversationHistory.push({
                    role: msg.role,
                    content: msg.content,
                    html: msg.metadata?.html,
                    toolCalls: msg.metadata?.toolCalls
                });
            });

            scrollToBottom();
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
    }
}

// 打开搜索对话框
function openSearchModal() {
    document.getElementById('searchModal').style.display = 'flex';
    document.getElementById('searchInput').focus();
}

// 关闭搜索对话框
function closeSearchModal() {
    document.getElementById('searchModal').style.display = 'none';
    document.getElementById('searchResults').innerHTML = '';
}

// 执行搜索
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        alert('请输入搜索关键词');
        return;
    }

    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading">搜索中...</div>';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query, limit: 50 })
        });

        const data = await response.json();

        if (response.ok) {
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<div class="no-results">未找到匹配的对话</div>';
                return;
            }

            // 清空并添加计数
            resultsDiv.innerHTML = '';
            const countDiv = document.createElement('div');
            countDiv.className = 'results-count';
            countDiv.textContent = `找到 ${data.count} 条结果`;
            resultsDiv.appendChild(countDiv);

            // 缓存正则表达式
            const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            const fragment = document.createDocumentFragment();

            data.results.forEach(result => {
                const resultItem = document.createElement('div');
                resultItem.className = 'search-result-item';

                const roleLabel = result.role === 'user' ? '用户' : 'Claude';
                const timestamp = new Date(result.timestamp).toLocaleString('zh-CN');

                // 高亮搜索关键词
                let highlightedContent = result.content;
                highlightedContent = highlightedContent.replace(regex, '<mark>$1</mark>');

                // 截取内容（最多显示 200 字符）
                if (highlightedContent.length > 200) {
                    const index = highlightedContent.toLowerCase().indexOf(query.toLowerCase());
                    const start = Math.max(0, index - 100);
                    const end = Math.min(highlightedContent.length, index + 100);
                    highlightedContent = '...' + highlightedContent.substring(start, end) + '...';
                }

                const header = document.createElement('div');
                header.className = 'result-header';
                header.innerHTML = `
                    <span class="result-role">${roleLabel}</span>
                    <span class="result-time">${timestamp}</span>
                `;

                const content = document.createElement('div');
                content.className = 'result-content';
                content.innerHTML = highlightedContent;

                resultItem.appendChild(header);
                resultItem.appendChild(content);
                fragment.appendChild(resultItem);
            });

            resultsDiv.appendChild(fragment);
        } else {
            resultsDiv.innerHTML = `<div class="error">搜索失败: ${data.error}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">搜索失败: ${error.message}</div>`;
    }
}

// 打开历史记录对话框
async function openHistoryModal() {
    document.getElementById('historyModal').style.display = 'flex';

    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '<div class="loading">加载中...</div>';

    try {
        const response = await fetch('/api/history?limit=50');
        const data = await response.json();

        if (response.ok) {
            if (data.history.length === 0) {
                historyList.innerHTML = '<div class="no-results">暂无历史记录</div>';
                return;
            }

            historyList.innerHTML = '';
            const fragment = document.createDocumentFragment();

            data.history.forEach(msg => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';

                const roleLabel = msg.role === 'user' ? '用户' : 'Claude';
                const timestamp = new Date(msg.timestamp).toLocaleString('zh-CN');

                // 截取内容
                let content = msg.content;
                if (content.length > 150) {
                    content = content.substring(0, 150) + '...';
                }

                const header = document.createElement('div');
                header.className = 'history-header';
                header.innerHTML = `
                    <span class="history-role">${roleLabel}</span>
                    <span class="history-time">${timestamp}</span>
                `;

                const contentDiv = document.createElement('div');
                contentDiv.className = 'history-content';
                contentDiv.textContent = content;

                historyItem.appendChild(header);
                historyItem.appendChild(contentDiv);
                fragment.appendChild(historyItem);
            });

            historyList.appendChild(fragment);
        } else {
            historyList.innerHTML = `<div class="error">加载失败: ${data.error}</div>`;
        }
    } catch (error) {
        historyList.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    }
}

// 关闭历史记录对话框
function closeHistoryModal() {
    document.getElementById('historyModal').style.display = 'none';
}

// 搜索输入框回车搜索
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
});

// 操作日志相关功能
let currentOperationsTab = 'all';

// 打开操作日志对话框
async function openOperationsModal() {
    document.getElementById('operationsModal').style.display = 'flex';
    await loadOperations('all');
}

// 关闭操作日志对话框
function closeOperationsModal() {
    document.getElementById('operationsModal').style.display = 'none';
}

// 切换操作日志标签
async function switchOperationsTab(tab, event) {
    currentOperationsTab = tab;

    // 更新标签样式
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }

    await loadOperations(tab);
}

// 加载操作日志
let operationsOffset = 0;
let operationsHasMore = true;
let operationsLoading = false;

async function loadOperations(status, append = false) {
    const operationsList = document.getElementById('operationsList');

    if (operationsLoading) return;
    operationsLoading = true;

    if (!append) {
        operationsOffset = 0;
        operationsHasMore = true;
        operationsList.innerHTML = '<div class="loading">加载中...</div>';
    } else {
        // 移除旧的"加载更多"按钮
        const oldLoadMore = operationsList.querySelector('.load-more');
        if (oldLoadMore) oldLoadMore.remove();
    }

    try {
        let url = `/api/operations/logs?limit=20&offset=${operationsOffset}`;
        if (status !== 'all') {
            url += `&status=${status}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (response.ok && data.success) {
            if (!append) {
                operationsList.innerHTML = '';
            }

            if (data.logs.length === 0) {
                if (!append) {
                    operationsList.innerHTML = '<div class="no-results">暂无操作记录</div>';
                }
                operationsHasMore = false;
                operationsLoading = false;
                return;
            }

            // 使用DocumentFragment批量插入
            const fragment = document.createDocumentFragment();

            data.logs.forEach(log => {
                const operationItem = document.createElement('div');
                operationItem.className = 'operation-item';

                const statusClass = log.status.toLowerCase();
                const statusText = {
                    'pending': '待审批',
                    'approved': '已批准',
                    'rejected': '已拒绝',
                    'executed': '已执行'
                }[log.status.toLowerCase()] || log.status;

                // 创建header
                const header = document.createElement('div');
                header.className = 'operation-header';
                header.innerHTML = `
                    <span class="operation-tool">${log.tool_name}</span>
                    <span class="operation-status ${statusClass}">${statusText}</span>
                `;

                // 创建预览（折叠JSON）
                const preview = document.createElement('div');
                preview.className = 'operation-preview collapsed';
                const jsonStr = JSON.stringify(log.input_data || {}, null, 2);
                const shortPreview = jsonStr.length > 100 ? jsonStr.substring(0, 100) + '...' : jsonStr;
                preview.textContent = shortPreview;
                preview.dataset.full = jsonStr;
                preview.dataset.short = shortPreview;
                preview.style.cursor = 'pointer';
                preview.onclick = function() {
                    if (this.classList.contains('collapsed')) {
                        this.textContent = this.dataset.full;
                        this.classList.remove('collapsed');
                    } else {
                        this.textContent = this.dataset.short;
                        this.classList.add('collapsed');
                    }
                };

                // 创建时间
                const time = document.createElement('div');
                time.className = 'operation-time';
                time.textContent = log.created_at || log.timestamp;

                operationItem.appendChild(header);
                operationItem.appendChild(preview);
                operationItem.appendChild(time);

                // 添加操作按钮
                if (log.status.toLowerCase() === 'pending') {
                    const actions = document.createElement('div');
                    actions.className = 'operation-actions';

                    const approveBtn = document.createElement('button');
                    approveBtn.className = 'approve-btn';
                    approveBtn.textContent = '批准';
                    approveBtn.onclick = () => approveOperation(log.id);

                    const rejectBtn = document.createElement('button');
                    rejectBtn.className = 'reject-btn';
                    rejectBtn.textContent = '拒绝';
                    rejectBtn.onclick = () => rejectOperation(log.id);

                    actions.appendChild(approveBtn);
                    actions.appendChild(rejectBtn);
                    operationItem.appendChild(actions);
                }

                fragment.appendChild(operationItem);
            });

            operationsList.appendChild(fragment);
            operationsOffset += data.logs.length;

            if (data.logs.length < 20) {
                operationsHasMore = false;
            }

            // 添加"加载更多"按钮
            if (operationsHasMore) {
                const loadMore = document.createElement('div');
                loadMore.className = 'load-more';
                loadMore.textContent = '加载更多...';
                loadMore.style.textAlign = 'center';
                loadMore.style.padding = '10px';
                loadMore.style.cursor = 'pointer';
                loadMore.style.color = '#007bff';
                loadMore.onclick = () => loadOperations(status, true);
                operationsList.appendChild(loadMore);
            }
        } else {
            operationsList.innerHTML = `<div class="error">加载失败: ${data.error || '未知错误'}</div>`;
        }
    } catch (error) {
        operationsList.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    } finally {
        operationsLoading = false;
    }
}

// 批准操作
async function approveOperation(logId) {
    if (!confirm('确定要批准此操作吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/operations/${logId}/approve`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok && data.success) {
            addSystemMessage('✓ 操作已批准并执行');
            await loadOperations(currentOperationsTab);
        } else {
            alert(`批准失败: ${data.error || '未知错误'}`);
        }
    } catch (error) {
        alert(`批准失败: ${error.message}`);
    }
}

// 批准权限
async function approvePermission(logId) {
    const permissionDiv = document.getElementById(`permission-${logId}`);
    if (!permissionDiv) return;

    try {
        const response = await fetch(`/api/operations/${logId}/approve`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // 更新UI显示已批准
            permissionDiv.innerHTML = `
                <div class="permission-header">✅ 已批准</div>
                <div class="permission-preview">操作已执行</div>
            `;
            permissionDiv.className = 'permission-approved';

            // 显示执行结果
            if (data.result) {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'tool-result';
                resultDiv.innerHTML = `
                    <div class="tool-result-header">📋 执行结果</div>
                    <pre class="tool-result-content">${JSON.stringify(data.result, null, 2)}</pre>
                `;
                permissionDiv.parentElement.appendChild(resultDiv);
            }
            scrollToBottom();
        } else {
            alert(`批准失败: ${data.error || '未知错误'}`);
        }
    } catch (error) {
        alert(`批准失败: ${error.message}`);
    }
}

// 拒绝权限
async function rejectPermission(logId) {
    const permissionDiv = document.getElementById(`permission-${logId}`);
    if (!permissionDiv) return;

    const reason = prompt('请输入拒绝原因（可选）：');
    if (reason === null) {
        return; // 用户取消
    }

    try {
        const response = await fetch(`/api/operations/${logId}/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason: reason || '用户拒绝' })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // 更新UI显示已拒绝
            permissionDiv.innerHTML = `
                <div class="permission-header">❌ 已拒绝</div>
                <div class="permission-preview">${reason || '用户拒绝'}</div>
            `;
            permissionDiv.className = 'permission-rejected';
            scrollToBottom();
        } else {
            alert(`拒绝失败: ${data.error || '未知错误'}`);
        }
    } catch (error) {
        alert(`拒绝失败: ${error.message}`);
    }
}

// 显示用户问题
function showUserQuestions(questions, containerDiv) {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'user-questions';

    questions.forEach((q, qIndex) => {
        const questionBlock = document.createElement('div');
        questionBlock.className = 'question-block';

        const questionHeader = document.createElement('div');
        questionHeader.className = 'question-header';
        questionHeader.innerHTML = `
            <span class="question-tag">${q.header}</span>
            <span class="question-text">${q.question}</span>
        `;
        questionBlock.appendChild(questionHeader);

        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'question-options';

        q.options.forEach((option, oIndex) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'question-option';

            const inputType = q.multiSelect ? 'checkbox' : 'radio';
            const inputName = `question_${qIndex}`;
            const inputId = `q${qIndex}_o${oIndex}`;

            optionDiv.innerHTML = `
                <input type="${inputType}" name="${inputName}" id="${inputId}" value="${option.label}">
                <label for="${inputId}">
                    <div class="option-label">${option.label}</div>
                    <div class="option-description">${option.description}</div>
                </label>
            `;

            optionsContainer.appendChild(optionDiv);
        });

        // 添加"其他"选项
        const otherDiv = document.createElement('div');
        otherDiv.className = 'question-option';
        const inputType = q.multiSelect ? 'checkbox' : 'radio';
        const inputName = `question_${qIndex}`;
        const otherId = `q${qIndex}_other`;

        otherDiv.innerHTML = `
            <input type="${inputType}" name="${inputName}" id="${otherId}" value="__other__">
            <label for="${otherId}">
                <div class="option-label">其他</div>
                <div class="option-description">自定义输入</div>
            </label>
            <input type="text" class="other-input" id="${otherId}_text" placeholder="请输入..." style="display:none; margin-top: 8px; width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        `;

        optionsContainer.appendChild(otherDiv);

        // 监听"其他"选项的选择
        setTimeout(() => {
            const otherCheckbox = document.getElementById(otherId);
            const otherInput = document.getElementById(`${otherId}_text`);

            if (otherCheckbox && otherInput) {
                otherCheckbox.addEventListener('change', function() {
                    otherInput.style.display = this.checked ? 'block' : 'none';
                    if (this.checked) {
                        otherInput.focus();
                    }
                });
            }
        }, 0);

        questionBlock.appendChild(optionsContainer);
        questionDiv.appendChild(questionBlock);
    });

    // 添加提交按钮
    const submitButton = document.createElement('button');
    submitButton.className = 'question-submit-btn';
    submitButton.textContent = '提交答案';
    submitButton.onclick = () => submitUserAnswers(questions, questionDiv);

    questionDiv.appendChild(submitButton);
    containerDiv.appendChild(questionDiv);
    scrollToBottom();
}

// 提交用户答案
async function submitUserAnswers(questions, questionDiv) {
    const answers = {};

    questions.forEach((q, qIndex) => {
        const inputName = `question_${qIndex}`;

        if (q.multiSelect) {
            // 多选
            const checked = document.querySelectorAll(`input[name="${inputName}"]:checked`);
            const values = [];
            checked.forEach(input => {
                if (input.value === '__other__') {
                    const otherText = document.getElementById(`${input.id}_text`).value.trim();
                    if (otherText) {
                        values.push(otherText);
                    }
                } else {
                    values.push(input.value);
                }
            });
            answers[q.header] = values.join(', ');
        } else {
            // 单选
            const selected = document.querySelector(`input[name="${inputName}"]:checked`);
            if (selected) {
                if (selected.value === '__other__') {
                    const otherText = document.getElementById(`${selected.id}_text`).value.trim();
                    answers[q.header] = otherText || '其他';
                } else {
                    answers[q.header] = selected.value;
                }
            }
        }
    });

    // 显示已提交的答案
    questionDiv.innerHTML = `
        <div class="question-answered">
            <div class="question-answered-header">✅ 已提交答案</div>
            <div class="question-answered-content">
                ${Object.entries(answers).map(([key, value]) =>
                    `<div><strong>${key}:</strong> ${value}</div>`
                ).join('')}
            </div>
        </div>
    `;
    scrollToBottom();

    // 构建答案文本
    const answerText = Object.entries(answers)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n');

    // 将答案作为 tool_result 发送回 Claude
    await continueConversationWithAnswers(answerText, answers);
}

// 继续对话（带用户答案）
async function continueConversationWithAnswers(answerText, answers) {
    try {
        // 添加用户答案到对话历史
        conversationHistory.push({
            role: 'user',
            content: answerText
        });

        // 保存用户答案到数据库
        await fetch('/api/save-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                role: 'user',
                content: answerText
            })
        });

        // 显示用户答案消息
        addMessage('user', answerText);

        // 显示输入指示器
        showTypingIndicator();

        // 继续对话
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: answerText,
                history: conversationHistory.slice(0, -1)
            })
        });

        removeTypingIndicator();

        if (!response.ok) {
            const error = await response.json();
            addMessage('assistant', `错误: ${error.error}`);
            return;
        }

        // 处理流式响应（复用现有逻辑）
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        chatContainer.appendChild(messageDiv);

        let fullResponse = '';
        let currentTextDiv = null;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'text') {
                            if (!currentTextDiv) {
                                currentTextDiv = document.createElement('div');
                                currentTextDiv.className = 'message-content';
                                messageDiv.appendChild(currentTextDiv);
                            }
                            fullResponse += data.content;
                            currentTextDiv.textContent = fullResponse;
                            scrollToBottom();
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                }
            }
        }

        // 保存 assistant 响应
        if (fullResponse) {
            conversationHistory.push({
                role: 'assistant',
                content: fullResponse
            });

            await fetch('/api/save-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    role: 'assistant',
                    content: fullResponse
                })
            });
        }

    } catch (error) {
        removeTypingIndicator();
        addMessage('assistant', `错误: ${error.message}`);
    }
}


