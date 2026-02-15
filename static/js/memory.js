// Memory 管理页面 JavaScript

let currentFilter = '';
let currentTag = null;
let currentViewingMemoryId = null;
let memories = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadMemories();
    loadTags();

    // 重要性滑块
    const importanceSlider = document.getElementById('memoryImportance');
    if (importanceSlider) {
        importanceSlider.addEventListener('input', function() {
            document.getElementById('importanceValue').textContent = this.value;
        });
    }
});

// 加载记忆列表
async function loadMemories() {
    try {
        let url = '/api/memory/memories';
        const params = new URLSearchParams();

        if (currentFilter) {
            params.append('memory_type', currentFilter);
        }
        if (currentTag) {
            params.append('tag', currentTag);
        }

        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            memories = data.memories;
            renderMemoriesList();
            document.getElementById('memoryStats').textContent = `共 ${memories.length} 条记忆`;
        } else {
            showError('加载记忆列表失败');
        }
    } catch (error) {
        showError('加载记忆列表失败: ' + error.message);
    }
}

// 渲染记忆列表
function renderMemoriesList() {
    const memoryList = document.getElementById('memoryList');

    if (memories.length === 0) {
        memoryList.innerHTML = '<div class="no-memories">暂无记忆，点击"添加记忆"开始记录</div>';
        return;
    }

    memoryList.innerHTML = memories.map(memory => {
        const tags = memory.tags || [];
        const importanceStars = renderImportanceStars(memory.importance || 1);
        const timeAgo = formatTimeAgo(memory.created_at);

        return `
            <div class="memory-item" onclick="viewMemory(${memory.id})">
                <div class="memory-item-header">
                    <span class="memory-item-title">${escapeHtml(memory.title || '无标题')}</span>
                    <div class="memory-item-meta">
                        <span class="memory-item-type ${memory.memory_type}">${memory.memory_type}</span>
                        <div class="memory-item-importance">${importanceStars}</div>
                    </div>
                </div>
                <div class="memory-item-content">${escapeHtml(memory.content)}</div>
                <div class="memory-item-footer">
                    <div class="memory-item-tags">
                        ${tags.slice(0, 3).map(tag =>
                            `<span class="memory-item-tag">${escapeHtml(tag)}</span>`
                        ).join('')}
                        ${tags.length > 3 ? `<span class="memory-item-tag">+${tags.length - 3}</span>` : ''}
                    </div>
                    <span class="memory-item-time">${timeAgo}</span>
                </div>
            </div>
        `;
    }).join('');
}

// 渲染重要性星星
function renderImportanceStars(importance) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        stars += `<span class="importance-star ${i <= importance ? 'filled' : ''}">★</span>`;
    }
    return stars;
}

// 格式化时间
function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;

    return date.toLocaleDateString('zh-CN');
}

// 加载标签
async function loadTags() {
    try {
        const response = await fetch('/api/memory/tags');
        const data = await response.json();

        if (data.success) {
            renderTagsList(data.tags);
        }
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

// 渲染标签列表
function renderTagsList(tags) {
    const tagsList = document.getElementById('tagsList');

    if (tags.length === 0) {
        tagsList.innerHTML = '<span style="color: #999; font-size: 12px;">暂无标签</span>';
        return;
    }

    tagsList.innerHTML = tags.map(tag => `
        <span class="tag-item ${currentTag === tag ? 'active' : ''}"
              onclick="filterByTag('${escapeHtml(tag)}')">
            ${escapeHtml(tag)}
        </span>
    `).join('');
}

// 搜索记忆
function searchMemories() {
    const query = document.getElementById('memorySearch').value.trim();

    if (!query) {
        loadMemories();
        return;
    }

    const filtered = memories.filter(m =>
        (m.title && m.title.toLowerCase().includes(query.toLowerCase())) ||
        (m.content && m.content.toLowerCase().includes(query.toLowerCase()))
    );

    memories = filtered;
    renderMemoriesList();
    document.getElementById('memoryStats').textContent = `找到 ${memories.length} 条记忆`;
}

// 类型筛选
function filterMemories() {
    const selected = document.querySelector('input[name="typeFilter"]:checked');
    currentFilter = selected ? selected.value : '';
    loadMemories();
}

// 标签筛选
function filterByTag(tag) {
    if (currentTag === tag) {
        currentTag = null;
    } else {
        currentTag = tag;
    }
    loadTags();
    loadMemories();
}

// 显示添加记忆模态框
function showAddMemoryModal() {
    document.getElementById('memoryModalTitle').textContent = '添加记忆';
    document.getElementById('editMemoryId').value = '';
    document.getElementById('memoryTitle').value = '';
    document.getElementById('memoryType').value = 'note';
    document.getElementById('memoryContent').value = '';
    document.getElementById('memoryTags').value = '';
    document.getElementById('memoryImportance').value = 3;
    document.getElementById('importanceValue').textContent = '3';

    document.getElementById('memoryModal').style.display = 'flex';
}

// 关闭记忆模态框
function closeMemoryModal() {
    document.getElementById('memoryModal').style.display = 'none';
}

// 保存记忆
async function saveMemory() {
    const memoryId = document.getElementById('editMemoryId').value;
    const title = document.getElementById('memoryTitle').value.trim();
    const memory_type = document.getElementById('memoryType').value;
    const content = document.getElementById('memoryContent').value.trim();
    const tagsText = document.getElementById('memoryTags').value.trim();
    const importance = parseInt(document.getElementById('memoryImportance').value);

    if (!content) {
        alert('请输入记忆内容');
        return;
    }

    const tags = tagsText ? tagsText.split(',').map(t => t.trim()).filter(t => t) : [];

    const data = {
        title: title || null,
        memory_type,
        content,
        tags: tags.length > 0 ? tags : null,
        importance
    };

    try {
        let response;
        if (memoryId) {
            response = await fetch(`/api/memory/memories/${memoryId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch('/api/memory/memories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        const result = await response.json();
        if (result.success) {
            closeMemoryModal();
            await loadMemories();
            await loadTags();
        } else {
            alert('保存失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

// 查看记忆详情
async function viewMemory(memoryId) {
    currentViewingMemoryId = memoryId;

    try {
        const response = await fetch(`/api/memory/memories/${memoryId}`);
        const data = await response.json();

        if (data.success) {
            showViewMemoryModal(data.memory);
        } else {
            alert('加载记忆详情失败');
        }
    } catch (error) {
        alert('加载记忆详情失败: ' + error.message);
    }
}

// 显示查看记忆模态框
function showViewMemoryModal(memory) {
    document.getElementById('viewMemoryTitle').textContent = memory.title || '无标题';

    const typeEl = document.getElementById('viewMemoryType');
    typeEl.textContent = memory.memory_type;
    typeEl.className = 'view-memory-type ' + memory.memory_type;

    document.getElementById('viewMemoryTime').textContent =
        new Date(memory.created_at).toLocaleString('zh-CN');
    document.getElementById('viewMemoryImportance').textContent =
        `重要性: ${'★'.repeat(memory.importance || 1)}`;

    const tagsEl = document.getElementById('viewMemoryTags');
    const tags = memory.tags || [];
    if (tags.length > 0) {
        tagsEl.innerHTML = tags.map(tag =>
            `<span class="view-memory-tag">${escapeHtml(tag)}</span>`
        ).join('');
        tagsEl.style.display = 'flex';
    } else {
        tagsEl.style.display = 'none';
    }

    document.getElementById('viewMemoryContent').textContent = memory.content;

    document.getElementById('viewMemoryModal').style.display = 'flex';
}

// 关闭查看记忆模态框
function closeViewMemoryModal() {
    document.getElementById('viewMemoryModal').style.display = 'none';
    currentViewingMemoryId = null;
}

// 编辑当前查看的记忆
function editViewedMemory() {
    if (!currentViewingMemoryId) return;

    const memory = memories.find(m => m.id === currentViewingMemoryId);
    if (!memory) return;

    closeViewMemoryModal();

    document.getElementById('memoryModalTitle').textContent = '编辑记忆';
    document.getElementById('editMemoryId').value = memory.id;
    document.getElementById('memoryTitle').value = memory.title || '';
    document.getElementById('memoryType').value = memory.memory_type;
    document.getElementById('memoryContent').value = memory.content;
    document.getElementById('memoryTags').value = (memory.tags || []).join(', ');
    document.getElementById('memoryImportance').value = memory.importance || 3;
    document.getElementById('importanceValue').textContent = memory.importance || 3;

    document.getElementById('memoryModal').style.display = 'flex';
}

// 删除当前查看的记忆
async function deleteViewedMemory() {
    if (!currentViewingMemoryId) return;
    if (!confirm('确定要删除这条记忆吗？')) return;

    try {
        const response = await fetch(`/api/memory/memories/${currentViewingMemoryId}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (result.success) {
            closeViewMemoryModal();
            await loadMemories();
            await loadTags();
        } else {
            alert('删除失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 导出记忆
async function exportMemories() {
    try {
        const response = await fetch('/api/memory/memories');
        const data = await response.json();

        if (data.success) {
            const exportData = {
                exported_at: new Date().toISOString(),
                memories: data.memories
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)],
                                  { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `memories_${new Date().toISOString().slice(0,10)}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } else {
            alert('导出失败');
        }
    } catch (error) {
        alert('导出失败: ' + error.message);
    }
}

// 导出为 Obsidian 格式
async function exportToObsidian() {
    try {
        const response = await fetch('/api/memory/export/obsidian', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_by: 'date' })
        });
        const data = await response.json();

        if (data.success) {
            // 创建一个 ZIP 文件或者逐个下载
            if (data.files && data.files.length > 0) {
                // 逐个下载文件
                for (const file of data.files) {
                    const blob = new Blob([file.content], { type: 'text/markdown' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = file.filename;
                    a.click();
                    URL.revokeObjectURL(url);
                    // 稍微延迟一下避免浏览器阻止多个下载
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                alert(`成功导出 ${data.total} 个 Obsidian 笔记！`);
            }
        } else {
            alert('导出失败: ' + (data.message || '未知错误'));
        }
    } catch (error) {
        alert('导出失败: ' + error.message);
    }
}

// 显示错误
function showError(message) {
    const memoryList = document.getElementById('memoryList');
    memoryList.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
}

// HTML 转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
