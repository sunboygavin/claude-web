#!/usr/bin/env python3
"""
测试 ask_user_question 工具的完整流程
"""

import json
import tools

# 测试 ask_user_question 工具
print("=" * 80)
print("测试 ask_user_question 工具")
print("=" * 80)

# 模拟 Claude 调用 ask_user_question
questions = [
    {
        "question": "是否要将更改推送到远程仓库？",
        "header": "Git Push",
        "multiSelect": False,
        "options": [
            {
                "label": "是的，立即推送",
                "description": "将所有提交推送到 GitHub 远程仓库"
            },
            {
                "label": "不，稍后再推",
                "description": "暂时不推送，保留在本地"
            }
        ]
    }
]

result = tools.execute_tool('ask_user_question', {'questions': questions})

print("\n工具执行结果:")
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("预期结果:")
print("=" * 80)
print("1. success: True")
print("2. requires_user_input: True")
print("3. questions: 包含问题数据")
print("\n这个结果会被发送到前端，前端会显示问题卡片")
print("用户选择答案后，答案会作为新消息发送回 Claude")
