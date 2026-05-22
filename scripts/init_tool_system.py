"""
初始化工具系统

将内置工具注册到系统中
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.registry.tool_registry import ToolRegistry


def init_tool_system():
    """初始化工具系统"""
    print("="*60)
    print("初始化工具系统")
    print("="*60)

    registry = ToolRegistry()

    # 注册内置工具
    builtin_tools = [
        {
            'name': 'read_file',
            'display_name': '读取文件',
            'description': '读取文件内容',
            'tool_type': 'builtin',
            'class_path': 'src.tools.file_tools.ReadTool',
            'permission_level': 'read',
            'tags': ['file', 'read'],
            'dangerous': False
        },
        {
            'name': 'write_file',
            'display_name': '写入文件',
            'description': '写入文件内容',
            'tool_type': 'builtin',
            'class_path': 'src.tools.file_tools.WriteTool',
            'permission_level': 'write',
            'tags': ['file', 'write'],
            'dangerous': False
        },
        {
            'name': 'edit_file',
            'display_name': '编辑文件',
            'description': '编辑文件内容（精确替换）',
            'tool_type': 'builtin',
            'class_path': 'src.tools.file_tools.EditTool',
            'permission_level': 'write',
            'tags': ['file', 'write', 'edit'],
            'dangerous': False
        },
        {
            'name': 'search_files',
            'display_name': '搜索文件',
            'description': '搜索文件（通配符模式）',
            'tool_type': 'builtin',
            'class_path': 'src.tools.search_tools.GlobTool',
            'permission_level': 'read',
            'tags': ['search', 'file'],
            'dangerous': False
        },
        {
            'name': 'search_code',
            'display_name': '搜索代码',
            'description': '搜索代码（正则表达式）',
            'tool_type': 'builtin',
            'class_path': 'src.tools.search_tools.GrepTool',
            'permission_level': 'read',
            'tags': ['search', 'code'],
            'dangerous': False
        },
        {
            'name': 'run_command',
            'display_name': '执行命令',
            'description': '执行Shell命令',
            'tool_type': 'builtin',
            'class_path': 'src.tools.shell_tools.BashTool',
            'permission_level': 'execute',
            'tags': ['shell', 'execute'],
            'dangerous': True
        },
        {
            'name': 'sub_agent',
            'display_name': '调用子Agent',
            'description': '调用其他Agent处理子任务',
            'tool_type': 'builtin',
            'class_path': 'src.tools.sub_agent_tool.SubAgentTool',
            'permission_level': 'agent_call',
            'tags': ['agent', 'collaboration'],
            'dangerous': False
        }
    ]

    print("\n注册内置工具:")
    for tool_info in builtin_tools:
        try:
            registry.register_tool(
                name=tool_info['name'],
                display_name=tool_info['display_name'],
                description=tool_info['description'],
                tool_type=tool_info['tool_type'],
                class_path=tool_info['class_path'],
                permission_level=tool_info['permission_level'],
                tags=tool_info['tags'],
                author='system',
                dangerous=tool_info['dangerous']
            )
            print(f"  ✓ {tool_info['name']}")
        except ValueError as e:
            print(f"  ⚠️  {tool_info['name']}: {e}")
        except Exception as e:
            print(f"  ✗ {tool_info['name']}: {e}")

    # 创建工具分组
    print("\n创建工具分组:")
    groups = {
        'file_operations': ['read_file', 'write_file', 'edit_file'],
        'search_operations': ['search_files', 'search_code'],
        'execution': ['run_command'],
        'collaboration': ['sub_agent']
    }

    for group_name, tools in groups.items():
        registry.create_group(group_name, tools)
        print(f"  ✓ {group_name}: {len(tools)}个工具")

    print("\n" + "="*60)
    print("工具系统初始化完成")
    print("="*60)
    print(f"\n已注册工具: {len(builtin_tools)}个")
    print(f"工具分组: {len(groups)}个")
    print(f"\n注册表位置: data/tools/registry.json")


if __name__ == '__main__':
    init_tool_system()
