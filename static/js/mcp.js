// MCP 配置页面 JavaScript

let currentServerId = null;
let servers = [];

// 预设服务器配置
const presetConfigs = {
    github: {
        name: 'GitHub',
        server_type: 'stdio',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-github'],
        env: {
            'GITHUB_PERSONAL_ACCESS_TOKEN': ''
        },
        config: null
    },
    filesystem: {
        name: '文件系统',
        server_type: 'stdio',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', '/root/claude-web'],
        env: {},
        config: null
    },
    git: {
        name: 'Git',
        server_type: 'stdio',
        command: 'uvx',
        args: ['mcp-server-git'],
        env: {},
        config: null
    },
    fetch: {
        name: 'Fetch',
        server_type: 'stdio',
        command: 'uvx',
        args: ['mcp-server-fetch'],
        env: {},
        config: null
    },
    notion: {
        name: 'Notion',
        server_type: 'stdio',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-notion'],
        env: {
            'NOTION_API_KEY': '',
            'NOTION_WORKSPACE_ID': ''
        },
        config: null
    },
    obsidian: {
        name: 'Obsidian',
        server_type: 'stdio',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', '/root/.openclaw/workspace/obsidian-vault'],
        env: {},
        config: null
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadServers();
});

// 加载服务器列表
async function loadServers() {
    try {
        const response = await fetch('/api/mcp/servers');
        const data = await response.json();

        if (data.success) {
            servers = data.servers;
            renderServerList();
        } else {
            showError('加载服务器列表失败');
        }
    } catch (error) {
        showError('加载服务器列表失败: ' + error.message);
    }
}

// 渲染服务器列表
function renderServerList() {
    const serverList = document.getElementById('serverList');

    if (servers.length === 0) {
        serverList.innerHTML = '<div class="no-servers">暂无服务器，点击上方按钮添加</div>';
        return;
    }

    serverList.innerHTML = servers.map(server => {
        const status = server.status?.status || 'unknown';
        const statusClass = status === 'connected' ? 'connected' :
                           status === 'error' ? 'error' :
                           status === 'disconnected' ? 'disconnected' : 'unknown';

        return `
            <div class="server-item ${currentServerId === server.id ? 'active' : ''}"
                 onclick="selectServer(${server.id})">
                <div class="server-item-header">
                    <span class="server-item-name">${escapeHtml(server.name)}</span>
                    <span class="server-item-type">${server.server_type}</span>
                </div>
                <div class="server-item-status">
                    <span class="status-dot ${statusClass}"></span>
                    <span>${status}</span>
                </div>
            </div>
        `;
    }).join('');
}

// 选择服务器
async function selectServer(serverId) {
    currentServerId = serverId;
    renderServerList();
    await loadServerDetail(serverId);
}

// 加载服务器详情
async function loadServerDetail(serverId) {
    try {
        const response = await fetch(`/api/mcp/servers/${serverId}`);
        const data = await response.json();

        if (data.success) {
            showServerDetail(data.server);
        } else {
            showError('加载服务器详情失败');
        }
    } catch (error) {
        showError('加载服务器详情失败: ' + error.message);
    }
}

// 显示服务器详情
function showServerDetail(server) {
    document.getElementById('mcpWelcome').style.display = 'none';
    document.getElementById('mcpDetail').style.display = 'block';

    document.getElementById('serverName').textContent = server.name;
    document.getElementById('serverType').textContent = server.server_type;
    document.getElementById('serverCommand').textContent = server.command || '-';
    document.getElementById('serverUrl').textContent = server.url || '-';

    // 显示状态
    const status = server.status?.status || 'unknown';
    const statusClass = status === 'connected' ? 'connected' :
                       status === 'error' ? 'error' :
                       status === 'disconnected' ? 'disconnected' : 'unknown';
    document.getElementById('serverStatus').innerHTML =
        `<span class="status-badge ${statusClass}">${status}</span>`;

    // 显示可用工具
    const toolsSection = document.getElementById('toolsSection');
    const toolsList = document.getElementById('toolsList');
    if (server.status?.available_tools && server.status.available_tools.length > 0) {
        toolsSection.style.display = 'block';
        toolsList.innerHTML = server.status.available_tools.map(tool =>
            `<div class="tool-item">${escapeHtml(tool)}</div>`
        ).join('');
    } else {
        toolsSection.style.display = 'none';
    }

    // 显示错误信息
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    if (server.status?.error_message) {
        errorSection.style.display = 'block';
        errorMessage.textContent = server.status.error_message;
    } else {
        errorSection.style.display = 'none';
    }
}

// 显示添加服务器模态框
function showAddServerModal() {
    document.getElementById('modalTitle').textContent = '添加服务器';
    document.getElementById('serverId').value = '';
    document.getElementById('inputName').value = '';
    document.getElementById('inputType').value = 'stdio';
    document.getElementById('inputCommand').value = '';
    document.getElementById('inputArgs').value = '';
    document.getElementById('inputEnv').value = '';
    document.getElementById('inputUrl').value = '';
    document.getElementById('inputConfig').value = '';
    document.getElementById('inputEnabled').checked = true;

    onTypeChange();
    document.getElementById('serverModal').style.display = 'flex';
}

// 编辑服务器
function editServer() {
    if (!currentServerId) return;

    const server = servers.find(s => s.id === currentServerId);
    if (!server) return;

    document.getElementById('modalTitle').textContent = '编辑服务器';
    document.getElementById('serverId').value = server.id;
    document.getElementById('inputName').value = server.name;
    document.getElementById('inputType').value = server.server_type;
    document.getElementById('inputCommand').value = server.command || '';
    document.getElementById('inputArgs').value = server.args ? JSON.stringify(server.args, null, 2) : '';
    document.getElementById('inputEnv').value = server.env ? JSON.stringify(server.env, null, 2) : '';
    document.getElementById('inputUrl').value = server.url || '';
    document.getElementById('inputConfig').value = server.config ? JSON.stringify(server.config, null, 2) : '';
    document.getElementById('inputEnabled').checked = server.enabled;

    onTypeChange();
    document.getElementById('serverModal').style.display = 'flex';
}

// 关闭服务器模态框
function closeServerModal() {
    document.getElementById('serverModal').style.display = 'none';
}

// 服务器类型变更时调整表单
function onTypeChange() {
    const type = document.getElementById('inputType').value;
    const commandGroup = document.getElementById('commandGroup');
    const argsGroup = document.getElementById('argsGroup');
    const envGroup = document.getElementById('envGroup');
    const urlGroup = document.getElementById('urlGroup');

    if (type === 'stdio') {
        commandGroup.style.display = 'block';
        argsGroup.style.display = 'block';
        envGroup.style.display = 'block';
        urlGroup.style.display = 'none';
    } else {
        commandGroup.style.display = 'none';
        argsGroup.style.display = 'none';
        envGroup.style.display = 'none';
        urlGroup.style.display = 'block';
    }
}

// 保存服务器
async function saveServer() {
    const serverId = document.getElementById('serverId').value;
    const name = document.getElementById('inputName').value.trim();
    const server_type = document.getElementById('inputType').value;
    const command = document.getElementById('inputCommand').value.trim() || null;
    const argsText = document.getElementById('inputArgs').value.trim();
    const envText = document.getElementById('inputEnv').value.trim();
    const url = document.getElementById('inputUrl').value.trim() || null;
    const configText = document.getElementById('inputConfig').value.trim();
    const enabled = document.getElementById('inputEnabled').checked;

    if (!name) {
        alert('请输入服务器名称');
        return;
    }

    // 解析 JSON
    let args = null;
    let env = null;
    let config = null;

    try {
        if (argsText) {
            args = JSON.parse(argsText);
        }
        if (envText) {
            env = JSON.parse(envText);
        }
        if (configText) {
            config = JSON.parse(configText);
        }
    } catch (error) {
        alert('JSON 格式错误: ' + error.message);
        return;
    }

    const data = {
        name,
        server_type,
        command,
        args,
        env,
        url,
        config,
        enabled
    };

    try {
        let response;
        if (serverId) {
            // 更新
            response = await fetch(`/api/mcp/servers/${serverId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            // 添加
            response = await fetch('/api/mcp/servers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        const result = await response.json();
        if (result.success) {
            closeServerModal();
            await loadServers();
            if (serverId) {
                await loadServerDetail(parseInt(serverId));
            }
        } else {
            alert('保存失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

// 删除服务器
async function deleteServer() {
    if (!currentServerId) return;
    if (!confirm('确定要删除这个服务器吗？')) return;

    try {
        const response = await fetch(`/api/mcp/servers/${currentServerId}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (result.success) {
            currentServerId = null;
            document.getElementById('mcpWelcome').style.display = 'block';
            document.getElementById('mcpDetail').style.display = 'none';
            await loadServers();
        } else {
            alert('删除失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 测试服务器连接
async function testServer() {
    if (!currentServerId) return;

    try {
        const response = await fetch(`/api/mcp/servers/${currentServerId}/test`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            alert('连接成功！');
            await loadServers();
            await loadServerDetail(currentServerId);
        } else {
            alert('连接失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        alert('连接失败: ' + error.message);
    }
}

// 重启服务器
async function restartServer() {
    if (!currentServerId) return;

    try {
        const response = await fetch(`/api/mcp/servers/${currentServerId}/restart`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            alert('重启成功！');
            await loadServers();
            await loadServerDetail(currentServerId);
        } else {
            alert('重启失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        alert('重启失败: ' + error.message);
    }
}

// 添加预设服务器
function addPresetServer(type) {
    const preset = presetConfigs[type];
    if (!preset) return;

    document.getElementById('modalTitle').textContent = '添加服务器';
    document.getElementById('serverId').value = '';
    document.getElementById('inputName').value = preset.name;
    document.getElementById('inputType').value = preset.server_type;
    document.getElementById('inputCommand').value = preset.command || '';
    document.getElementById('inputArgs').value = preset.args ? JSON.stringify(preset.args, null, 2) : '';
    document.getElementById('inputEnv').value = preset.env ? JSON.stringify(preset.env, null, 2) : '';
    document.getElementById('inputUrl').value = preset.url || '';
    document.getElementById('inputConfig').value = preset.config ? JSON.stringify(preset.config, null, 2) : '';
    document.getElementById('inputEnabled').checked = true;

    onTypeChange();
    document.getElementById('serverModal').style.display = 'flex';
}

// 关闭凭证模态框
function closeCredentialModal() {
    document.getElementById('credentialModal').style.display = 'none';
}

// 显示错误
function showError(message) {
    const serverList = document.getElementById('serverList');
    serverList.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
