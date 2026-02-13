#!/usr/bin/env python3
"""
测试新功能的脚本
"""

import sys
sys.path.insert(0, '/root/claude-web')

import config
import tools

def test_config():
    """测试配置"""
    print("=" * 50)
    print("测试配置")
    print("=" * 50)
    print(f"可用模型: {list(config.AVAILABLE_MODELS.keys())}")
    print(f"默认模型: {config.DEFAULT_MODEL}")
    print(f"模型映射:")
    for name, model_id in config.AVAILABLE_MODELS.items():
        print(f"  {name}: {model_id}")
    print()

def test_tools():
    """测试工具"""
    print("=" * 50)
    print("测试工具")
    print("=" * 50)
    print(f"工具数量: {len(tools.TOOLS)}")
    print("工具列表:")
    for tool in tools.TOOLS:
        print(f"  - {tool['name']}: {tool['description']}")
    print()

def test_web_fetch():
    """测试 web_fetch"""
    print("=" * 50)
    print("测试 Web Fetch")
    print("=" * 50)
    result = tools.execute_web_fetch("https://example.com", "获取页面标题")
    if result['success']:
        print(f"✓ Web Fetch 成功")
        print(f"  URL: {result['url']}")
        print(f"  内容长度: {len(result['content'])} 字符")
        print(f"  内容预览: {result['content'][:200]}...")
    else:
        print(f"✗ Web Fetch 失败: {result['error']}")
    print()

def test_list_directory():
    """测试 list_directory"""
    print("=" * 50)
    print("测试 List Directory")
    print("=" * 50)
    result = tools.execute_list_directory("/root/claude-web")
    if result['success']:
        print(f"✓ List Directory 成功")
        print(f"  路径: {result['path']}")
        print(f"  项目数: {len(result['items'])}")
        print("  前 5 个项目:")
        for item in result['items'][:5]:
            print(f"    - {item['name']} ({item['type']})")
    else:
        print(f"✗ List Directory 失败: {result['error']}")
    print()

if __name__ == '__main__':
    print("\n🚀 Claude Web 功能测试\n")

    test_config()
    test_tools()
    test_list_directory()
    test_web_fetch()

    print("=" * 50)
    print("✓ 所有测试完成！")
    print("=" * 50)
