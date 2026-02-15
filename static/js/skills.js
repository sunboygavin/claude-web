// Skills 管理页面 JavaScript

let currentSkillId = null;
let skills = [];

// 技能模板
const skillTemplates = {
    python: {
        name: '新 Python 技能',
        skill_type: 'python',
        description: '一个 Python 技能',
        code: `"""
Python 技能模板
"""

class MySkill:
    """我的技能类"""

    @staticmethod
    def execute(input_data):
        """
        执行技能

        Args:
            input_data: 输入数据字典

        Returns:
            结果字典
        """
        # 在这里编写你的技能逻辑
        name = input_data.get('name', 'World')

        return {
            'result': f'Hello, {name}!',
            'success': True
        }

# 技能导出
skill = MySkill()
`
    },
    tool: {
        name: '新工具技能',
        skill_type: 'tool',
        description: '一个工具包装技能',
        code: `"""
工具包装技能模板
用于包装系统工具或外部命令
"""

import subprocess
import json

class ToolSkill:
    """工具技能类"""

    @staticmethod
    def execute(input_data):
        """
        执行工具命令

        Args:
            input_data: 输入数据字典

        Returns:
            结果字典
        """
        command = input_data.get('command', '')
        args = input_data.get('args', [])

        try:
            result = subprocess.run(
                [command] + args,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'success': result.returncode == 0
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

# 技能导出
skill = ToolSkill()
`
    },
    transform: {
        name: '新数据转换技能',
        skill_type: 'transform',
        description: '一个数据转换技能',
        code: `"""
数据转换技能模板
用于处理和转换数据格式
"""

import json

class TransformSkill:
    """数据转换技能类"""

    @staticmethod
    def execute(input_data):
        """
        转换数据

        Args:
            input_data: 输入数据字典

        Returns:
            转换后的数据
        """
        data = input_data.get('data', {})
        transform_type = input_data.get('transform', 'uppercase')

        result = {}

        if transform_type == 'uppercase':
            # 转换为大写
            for key, value in data.items():
                if isinstance(value, str):
                    result[key] = value.upper()
                else:
                    result[key] = value

        elif transform_type == 'lowercase':
            # 转换为小写
            for key, value in data.items():
                if isinstance(value, str):
                    result[key] = value.lower()
                else:
                    result[key] = value

        elif transform_type == 'json':
            # JSON 格式化
            result = {
                'original': data,
                'formatted': json.dumps(data, indent=2, ensure_ascii=False)
            }

        return {
            'result': result,
            'transform': transform_type,
            'success': True
        }

# 技能导出
skill = TransformSkill()
`
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadSkills();
});

// 加载技能列表
async function loadSkills() {
    try {
        const response = await fetch('/api/skills/skills');
        const data = await response.json();

        if (data.success) {
            skills = data.skills;
            renderSkillsList();
        } else {
            showError('加载技能列表失败');
        }
    } catch (error) {
        showError('加载技能列表失败: ' + error.message);
    }
}

// 渲染技能列表
function renderSkillsList() {
    const skillsList = document.getElementById('skillsList');

    if (skills.length === 0) {
        skillsList.innerHTML = '<div class="no-skills">暂无技能，点击上方按钮创建</div>';
        return;
    }

    skillsList.innerHTML = skills.map(skill => `
        <div class="skill-item ${currentSkillId === skill.id ? 'active' : ''}"
             onclick="selectSkill(${skill.id})">
            <div class="skill-item-header">
                <span class="skill-item-name">${escapeHtml(skill.name)}</span>
                <span class="skill-item-type">${skill.skill_type}</span>
            </div>
            <div class="skill-item-desc">${escapeHtml(skill.description || '无描述')}</div>
        </div>
    `).join('');
}

// 选择技能
async function selectSkill(skillId) {
    currentSkillId = skillId;
    renderSkillsList();
    await loadSkillDetail(skillId);
}

// 加载技能详情
async function loadSkillDetail(skillId) {
    try {
        const response = await fetch(`/api/skills/skills/${skillId}`);
        const data = await response.json();

        if (data.success) {
            showSkillEditor(data.skill);
        } else {
            showError('加载技能详情失败');
        }
    } catch (error) {
        showError('加载技能详情失败: ' + error.message);
    }
}

// 显示技能编辑器
function showSkillEditor(skill) {
    document.getElementById('skillsWelcome').style.display = 'none';
    document.getElementById('skillsEditor').style.display = 'flex';

    document.getElementById('skillName').value = skill.name;
    document.getElementById('skillType').value = skill.skill_type;
    document.getElementById('skillCode').value = skill.code || '';
    document.getElementById('skillDescription').value = skill.description || '';
    document.getElementById('skillConfig').value = skill.config ? JSON.stringify(skill.config, null, 2) : '';
    document.getElementById('skillEnabled').checked = skill.enabled;
}

// 切换标签页
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.editor-tabs .tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(`tab-${tabName}`).style.display = 'flex';
    document.querySelector(`.editor-tabs .tab-btn[data-tab="${tabName}"]`).classList.add('active');
}

// 显示添加技能模态框
function showAddSkillModal() {
    document.getElementById('skillModalTitle').textContent = '创建技能';
    document.getElementById('editSkillId').value = '';
    document.getElementById('modalSkillName').value = '';
    document.getElementById('modalSkillType').value = 'python';
    document.getElementById('modalSkillDescription').value = '';

    document.getElementById('skillModal').style.display = 'flex';
}

// 关闭技能模态框
function closeSkillModal() {
    document.getElementById('skillModal').style.display = 'none';
}

// 从模板创建
function createFromTemplate(templateType) {
    const template = skillTemplates[templateType];
    if (!template) return;

    document.getElementById('skillModalTitle').textContent = '从模板创建';
    document.getElementById('editSkillId').value = '';
    document.getElementById('modalSkillName').value = template.name;
    document.getElementById('modalSkillType').value = template.skill_type;
    document.getElementById('modalSkillDescription').value = template.description;

    document.getElementById('skillModal').style.display = 'flex';

    window.pendingTemplateCode = template.code;
}

// 创建技能
async function createSkill() {
    const name = document.getElementById('modalSkillName').value.trim();
    const skill_type = document.getElementById('modalSkillType').value;
    const description = document.getElementById('modalSkillDescription').value.trim();

    if (!name) {
        alert('请输入技能名称');
        return;
    }

    const code = window.pendingTemplateCode || skillTemplates[skill_type]?.code || '';

    const data = {
        name,
        skill_type,
        description,
        code,
        config: null,
        enabled: true
    };

    try {
        const response = await fetch('/api/skills/skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            closeSkillModal();
            await loadSkills();
            await selectSkill(result.skill_id);
        } else {
            alert('创建失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('创建失败: ' + error.message);
    }
}

// 保存技能
async function saveSkill() {
    if (!currentSkillId) return;

    const name = document.getElementById('skillName').value.trim();
    const skill_type = document.getElementById('skillType').value;
    const code = document.getElementById('skillCode').value;
    const description = document.getElementById('skillDescription').value.trim();
    const configText = document.getElementById('skillConfig').value.trim();
    const enabled = document.getElementById('skillEnabled').checked;

    if (!name) {
        alert('请输入技能名称');
        return;
    }

    let config = null;
    if (configText) {
        try {
            config = JSON.parse(configText);
        } catch (error) {
            alert('配置 JSON 格式错误: ' + error.message);
            return;
        }
    }

    const data = {
        name,
        skill_type,
        code,
        description,
        config,
        enabled
    };

    try {
        const response = await fetch(`/api/skills/skills/${currentSkillId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            alert('保存成功！');
            await loadSkills();
        } else {
            alert('保存失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

// 删除技能
async function deleteSkill() {
    if (!currentSkillId) return;
    if (!confirm('确定要删除这个技能吗？')) return;

    try {
        const response = await fetch(`/api/skills/skills/${currentSkillId}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (result.success) {
            currentSkillId = null;
            document.getElementById('skillsWelcome').style.display = 'block';
            document.getElementById('skillsEditor').style.display = 'none';
            await loadSkills();
        } else {
            alert('删除失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 测试技能
function testSkill() {
    if (!currentSkillId) return;
    document.getElementById('testInput').value = '{"name": "Test"}';
    document.getElementById('testOutput').textContent = '等待测试...';
    document.getElementById('testModal').style.display = 'flex';
}

// 关闭测试模态框
function closeTestModal() {
    document.getElementById('testModal').style.display = 'none';
}

// 运行技能测试
async function runSkillTest() {
    if (!currentSkillId) return;

    const inputText = document.getElementById('testInput').value.trim();
    let input_data;

    try {
        input_data = inputText ? JSON.parse(inputText) : {};
    } catch (error) {
        alert('输入 JSON 格式错误: ' + error.message);
        return;
    }

    document.getElementById('testOutput').textContent = '正在测试...';

    try {
        const response = await fetch(`/api/skills/skills/${currentSkillId}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: input_data })
        });

        const result = await response.json();
        if (result.success) {
            document.getElementById('testOutput').textContent =
                JSON.stringify(result.result, null, 2);
        } else {
            document.getElementById('testOutput').textContent =
                '错误: ' + (result.error || '未知错误');
        }
    } catch (error) {
        document.getElementById('testOutput').textContent =
            '错误: ' + error.message;
    }
}

// 显示错误
function showError(message) {
    const skillsList = document.getElementById('skillsList');
    skillsList.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
