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
    setTimeout(() => {
        scrollToBottom();
    }, 100);
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
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory.slice(0, -1)
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

                        } else if (data.type === 'tool_result') {
                            // 工具结果
                            const resultDiv = document.createElement('div');
                            resultDiv.className = 'tool-result';

                            let resultContent = '';
                            if (data.result.success) {
                                resultContent = data.result.output || data.result.content || data.result.message || JSON.stringify(data.result, null, 2);
                            } else {
                                resultContent = `❌ Error: ${data.result.error}`;
                            }

                            resultDiv.innerHTML = `
                                <div class="tool-result-header">📋 Result</div>
                                <pre class="tool-result-content">${resultContent}</pre>
                            `;
                            messageDiv.appendChild(resultDiv);
                            scrollToBottom();

                            // 重置文本容器，为后续文本做准备
                            currentTextDiv = null;

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

        conversationHistory.push({ role: 'assistant', content: fullResponse });

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

                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = msg.content;

                messageDiv.appendChild(contentDiv);
                chatContainer.appendChild(messageDiv);

                // 添加到内存中的历史记录
                conversationHistory.push({
                    role: msg.role,
                    content: msg.content
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

            resultsDiv.innerHTML = `<div class="results-count">找到 ${data.count} 条结果</div>`;

            data.results.forEach(result => {
                const resultItem = document.createElement('div');
                resultItem.className = 'search-result-item';

                const roleLabel = result.role === 'user' ? '用户' : 'Claude';
                const timestamp = new Date(result.timestamp).toLocaleString('zh-CN');

                // 高亮搜索关键词
                let highlightedContent = result.content;
                const regex = new RegExp(`(${query})`, 'gi');
                highlightedContent = highlightedContent.replace(regex, '<mark>$1</mark>');

                // 截取内容（最多显示 200 字符）
                if (highlightedContent.length > 200) {
                    const index = highlightedContent.toLowerCase().indexOf(query.toLowerCase());
                    const start = Math.max(0, index - 100);
                    const end = Math.min(highlightedContent.length, index + 100);
                    highlightedContent = '...' + highlightedContent.substring(start, end) + '...';
                }

                resultItem.innerHTML = `
                    <div class="result-header">
                        <span class="result-role">${roleLabel}</span>
                        <span class="result-time">${timestamp}</span>
                    </div>
                    <div class="result-content">${highlightedContent}</div>
                `;

                resultsDiv.appendChild(resultItem);
            });
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
        const response = await fetch('/api/history?limit=100');
        const data = await response.json();

        if (response.ok) {
            if (data.history.length === 0) {
                historyList.innerHTML = '<div class="no-results">暂无历史记录</div>';
                return;
            }

            historyList.innerHTML = '';

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

                historyItem.innerHTML = `
                    <div class="history-header">
                        <span class="history-role">${roleLabel}</span>
                        <span class="history-time">${timestamp}</span>
                    </div>
                    <div class="history-content">${content}</div>
                `;

                historyList.appendChild(historyItem);
            });
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

