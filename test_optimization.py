#!/usr/bin/env python3
"""
Claude Web v2.2.0 功能测试脚本
测试所有优化后的工具功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/claude-web')

import tools
import system_prompt
import database

def test_bash_timeout():
    """测试 bash 超时参数"""
    print("测试 1: Bash 超时参数...")
    result = tools.execute_bash('echo "test"', timeout=5000)
    assert result['success'], "Bash 执行失败"
    print("  ✓ Bash 超时参数正常")

def test_read_file_pagination():
    """测试文件分页读取"""
    print("\n测试 2: 文件分页读取...")
    result = tools.execute_read_file('/root/claude-web/config.py', offset=0, limit=10)
    assert result['success'], "文件读取失败"
    assert 'total_lines' in result, "缺少总行数信息"
    assert 'offset' in result, "缺少 offset 信息"
    print(f"  ✓ 读取成功，总行数: {result['total_lines']}")

def test_edit_file_replace_all():
    """测试批量替换"""
    print("\n测试 3: 批量替换功能...")
    # 创建测试文件
    test_file = '/tmp/test_edit.txt'
    with open(test_file, 'w') as f:
        f.write("test test test")

    result = tools.execute_edit_file(test_file, 'test', 'demo', replace_all=True)
    assert result['success'], "编辑失败"
    assert result['replacements'] == 3, "替换次数不正确"

    # 验证结果
    with open(test_file, 'r') as f:
        content = f.read()
    assert content == "demo demo demo", "替换结果不正确"

    os.remove(test_file)
    print("  ✓ 批量替换正常")

def test_grep_output_modes():
    """测试 grep 输出模式"""
    print("\n测试 4: Grep 输出模式...")

    # 测试 files_with_matches 模式
    result = tools.execute_grep('def', path='/root/claude-web/tools.py',
                                output_mode='files_with_matches')
    assert result['success'], "Grep files_with_matches 失败"
    assert 'files' in result, "缺少 files 字段"
    print(f"  ✓ files_with_matches 模式: 找到 {result['count']} 个文件")

    # 测试 count 模式
    result = tools.execute_grep('def', path='/root/claude-web/tools.py',
                                output_mode='count')
    assert result['success'], "Grep count 失败"
    assert 'results' in result, "缺少 results 字段"
    print(f"  ✓ count 模式: {result['total_files']} 个文件")

    # 测试 content 模式
    result = tools.execute_grep('def execute_bash', path='/root/claude-web/tools.py',
                                output_mode='content')
    assert result['success'], "Grep content 失败"
    assert 'results' in result, "缺少 results 字段"
    print(f"  ✓ content 模式: {result['count']} 个匹配")

def test_grep_case_insensitive():
    """测试大小写不敏感搜索"""
    print("\n测试 5: 大小写不敏感搜索...")
    result = tools.execute_grep('ANTHROPIC', path='/root/claude-web/config.py',
                                case_insensitive=True, output_mode='files_with_matches')
    assert result['success'], "大小写不敏感搜索失败"
    print("  ✓ 大小写不敏感搜索正常")

def test_grep_context():
    """测试上下文显示"""
    print("\n测试 6: 上下文显示...")
    result = tools.execute_grep('def execute_bash', path='/root/claude-web/tools.py',
                                output_mode='content', context=2)
    assert result['success'], "上下文显示失败"
    if result['results']:
        assert '\n' in result['results'][0]['content'], "缺少上下文行"
    print("  ✓ 上下文显示正常")

def test_system_prompt():
    """测试系统提示词"""
    print("\n测试 7: 系统提示词...")
    prompt = system_prompt.get_system_prompt()
    assert len(prompt) > 100, "系统提示词太短"
    assert 'Claude Code' in prompt, "系统提示词缺少关键内容"
    print(f"  ✓ 系统提示词正常 ({len(prompt)} 字符)")

def test_database_context_manager():
    """测试数据库上下文管理器"""
    print("\n测试 8: 数据库上下文管理器...")
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
        print(f"  ✓ 数据库连接正常 ({count} 条记录)")
    except Exception as e:
        print(f"  ✗ 数据库连接失败: {e}")
        raise

def test_all_tools_available():
    """测试所有工具定义"""
    print("\n测试 9: 工具定义...")
    expected_tools = ['bash', 'read_file', 'write_file', 'edit_file',
                     'glob', 'grep', 'list_directory', 'web_fetch', 'web_search']

    tool_names = [tool['name'] for tool in tools.TOOLS]
    for tool in expected_tools:
        assert tool in tool_names, f"缺少工具: {tool}"

    print(f"  ✓ 所有 {len(tools.TOOLS)} 个工具定义正常")

def test_tool_parameters():
    """测试工具参数定义"""
    print("\n测试 10: 工具参数...")

    # 检查 bash 的 timeout 参数
    bash_tool = next(t for t in tools.TOOLS if t['name'] == 'bash')
    assert 'timeout' in bash_tool['input_schema']['properties'], "Bash 缺少 timeout 参数"

    # 检查 read_file 的分页参数
    read_tool = next(t for t in tools.TOOLS if t['name'] == 'read_file')
    assert 'offset' in read_tool['input_schema']['properties'], "Read 缺少 offset 参数"
    assert 'limit' in read_tool['input_schema']['properties'], "Read 缺少 limit 参数"

    # 检查 edit_file 的 replace_all 参数
    edit_tool = next(t for t in tools.TOOLS if t['name'] == 'edit_file')
    assert 'replace_all' in edit_tool['input_schema']['properties'], "Edit 缺少 replace_all 参数"

    # 检查 grep 的新参数
    grep_tool = next(t for t in tools.TOOLS if t['name'] == 'grep')
    assert 'output_mode' in grep_tool['input_schema']['properties'], "Grep 缺少 output_mode 参数"
    assert 'case_insensitive' in grep_tool['input_schema']['properties'], "Grep 缺少 case_insensitive 参数"
    assert 'context' in grep_tool['input_schema']['properties'], "Grep 缺少 context 参数"

    print("  ✓ 所有工具参数定义正常")

def main():
    """运行所有测试"""
    print("=" * 60)
    print("Claude Web v2.2.0 功能测试")
    print("=" * 60)

    try:
        test_bash_timeout()
        test_read_file_pagination()
        test_edit_file_replace_all()
        test_grep_output_modes()
        test_grep_case_insensitive()
        test_grep_context()
        test_system_prompt()
        test_database_context_manager()
        test_all_tools_available()
        test_tool_parameters()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
