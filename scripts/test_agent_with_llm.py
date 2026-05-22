#!/usr/bin/env python3
"""
使用真实LLM测试象棋游戏开发工作流

现在LLM已配置，测试Agent真正调用LLM生成代码
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "🚀"*30)
    print("使用真实LLM测试 - 象棋游戏开发")
    print("🚀"*30)

    # 步骤1: 初始化MCP系统
    print("\n步骤1: 初始化MCP系统...")
    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    manager = MCPServerManager()
    manager.start_all_servers()
    mcp_tools = create_mcp_tools(manager)
    print(f"✓ MCP系统启动成功 ({len(mcp_tools)} 个工具)")

    # 步骤2: 获取项目信息
    print("\n步骤2: 获取项目信息...")
    from src.project_manager import ProjectManager

    user_id = 'user_test'
    proj_mgr = ProjectManager(user_id=user_id)

    if not proj_mgr.project_exists('chess_game'):
        print("✗ 项目不存在")
        return 1

    project = proj_mgr.get_project('chess_game')
    workspace_dir = proj_mgr.get_project_workspace('chess_game')
    print(f"✓ 项目: {project.project_id}")
    print(f"  工作空间: {workspace_dir}")

    # 步骤3: 创建任务
    print("\n步骤3: 创建开发任务...")
    from src.workflow.task import Task

    task = Task(
        task_id='chess_game_llm_001',
        title='开发单机象棋游戏',
        description=f'''
请开发一个简单的单机象棋游戏，要求：

功能需求：
1. 基本的象棋规则（将、士、象、马、车、炮、兵）
2. 棋盘显示（10x9格子）
3. 红黑双方轮流走棋
4. 基本的走棋规则验证
5. 简单的AI对手（随机走棋）
6. 胜负判断（将帅被吃）

技术要求：
1. 使用Python实现
2. 命令行界面（文本显示）
3. 代码结构清晰，易于理解
4. 包含基本的测试

交付物：
1. 源代码文件
2. README说明文档
3. 运行示例

重要：所有代码必须生成到项目工作空间：{workspace_dir}
'''
    )

    print(f"✓ 任务创建成功")
    print(f"  任务ID: {task.task_id}")

    # 步骤4: 创建带LLM的Agent
    print("\n步骤4: 创建带LLM的Agent...")
    from src.agents.generic_agent import GenericAgent

    agents = []

    # Requester Agent
    requester_config = {
        'name': 'requester',
        'role': '需求分析师',
        'description': '分析和澄清需求',
        'system_prompt': '''你是需求分析师。分析用户需求，输出需求分析报告。

请分析任务需求，输出JSON格式：
{
    "analysis": "需求分析（简短）",
    "requirements": ["需求1", "需求2", "需求3"],
    "feasibility": "可行性评估（一句话）",
    "suggestions": ["建议1", "建议2"],
    "output": "分析结果（一句话）",
    "next_agent": "product_manager"
}

注意：保持简洁，每项不超过50字。''',
        'llm': {
            'provider': 'claude',
            'model': 'claude-sonnet-4-5'
        },
        'tools': {'inherit_global': False, 'whitelist': []}
    }
    agents.append(GenericAgent(name='requester', config=requester_config))

    # Product Manager Agent
    pm_config = {
        'name': 'product_manager',
        'role': '产品经理',
        'description': '规划产品功能',
        'system_prompt': '''你是产品经理。规划功能，输出功能规划。

输出JSON格式：
{
    "features": [
        {"name": "功能1", "priority": "P0", "description": "描述"},
        {"name": "功能2", "priority": "P0", "description": "描述"}
    ],
    "milestones": ["M1: 里程碑1", "M2: 里程碑2"],
    "output": "功能规划完成",
    "next_agent": "architect"
}

注意：保持简洁，3-5个核心功能即可。''',
        'llm': {
            'provider': 'claude',
            'model': 'claude-sonnet-4-5'
        },
        'tools': {'inherit_global': False, 'whitelist': []}
    }
    agents.append(GenericAgent(name='product_manager', config=pm_config))

    # Architect Agent
    architect_config = {
        'name': 'architect',
        'role': '架构师',
        'description': '设计系统架构',
        'system_prompt': '''你是架构师。设计架构，输出架构设计。

输出JSON格式：
{
    "modules": [
        {"name": "模块1.py", "description": "描述"},
        {"name": "模块2.py", "description": "描述"}
    ],
    "class_design": {"类名1": "描述", "类名2": "描述"},
    "tech_stack": "Python 3.10+",
    "output": "架构设计完成",
    "next_agent": "developer"
}

注意：保持简洁，4-6个核心模块。''',
        'llm': {
            'provider': 'claude',
            'model': 'claude-sonnet-4-5'
        },
        'tools': {'inherit_global': False, 'whitelist': []}
    }
    agents.append(GenericAgent(name='architect', config=architect_config))

    # Developer Agent（简化版，只生成一个文件作为演示）
    developer_config = {
        'name': 'developer',
        'role': '开发工程师',
        'description': '编写代码',
        'system_prompt': f'''你是开发工程师。根据架构设计编写代码。

重要：这是一个演示，只需要生成一个简单的main.py文件即可。

输出JSON格式：
{{
    "code": "# Python代码内容\\nprint('Hello Chess Game')",
    "filename": "main.py",
    "output": "代码编写完成",
    "next_agent": null
}}

注意：
1. code字段包含完整的Python代码
2. 代码要简单但可运行
3. 包含基本的注释''',
        'llm': {
            'provider': 'claude',
            'model': 'claude-sonnet-4-5'
        },
        'tools': {
            'inherit_global': False,
            'whitelist': [
                'mcp__filesystem__write_file',
                'mcp__filesystem__create_directory'
            ]
        }
    }
    agents.append(GenericAgent(name='developer', config=developer_config))

    print(f"✓ 创建了 {len(agents)} 个Agent")
    for agent in agents:
        llm_status = "✓ LLM已配置" if agent.llm_client else "✗ 无LLM"
        print(f"  - {agent.name} ({agent.role}) {llm_status}")

    # 步骤5: 为Developer添加MCP工具
    print("\n步骤5: 为Developer配置MCP工具...")
    from src.registry.tool_registry import ToolRegistry

    registry = ToolRegistry()
    for tool_name, tool in mcp_tools.items():
        if not registry.get(tool_name):
            metadata = {
                'name': tool_name,
                'display_name': tool.get_name(),
                'description': tool.get_description(),
                'type': 'mcp',
                'enabled': True
            }
            registry.register(tool_name, metadata)

    developer = agents[3]
    file_tools = [
        'mcp__filesystem__write_file',
        'mcp__filesystem__create_directory'
    ]

    added_count = 0
    for tool_name in file_tools:
        if tool_name in mcp_tools:
            tool = mcp_tools[tool_name]
            if hasattr(developer, 'tool_registry') and developer.tool_registry:
                developer.tool_registry.tools[tool_name] = tool
                added_count += 1

    print(f"✓ 为Developer添加了 {added_count} 个MCP工具")

    # 步骤6: 执行简化的工作流（只测试Requester）
    print("\n步骤6: 测试Requester Agent...")
    print("="*60)

    requester = agents[0]

    try:
        result = requester.process(task)

        print(f"\n✓ Requester执行成功")
        print(f"\n输出内容:")
        print("-"*60)
        if isinstance(result, dict):
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
        print("-"*60)

    except Exception as e:
        print(f"\n✗ Requester执行失败: {e}")
        import traceback
        traceback.print_exc()

    # 清理
    print("\n正在关闭MCP系统...")
    manager.shutdown_all_servers()

    print("\n" + "="*60)
    print("✓ 测试完成！")
    print("="*60)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
