#!/usr/bin/env python3
"""
使用真实项目系统测试象棋游戏开发工作流

完全使用项目管理系统：
1. 通过ProjectManager创建项目
2. 通过CollaborativeOrchestrator执行Agent协作
3. 代码生成到正确的workspace目录
4. 验证完整的端到端流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "🚀"*30)
    print("使用真实项目系统测试 - 象棋游戏开发")
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

    # 检查项目是否已存在
    if proj_mgr.project_exists('chess_game'):
        print("✓ 项目已存在: chess_game")
        project = proj_mgr.get_project('chess_game')
    else:
        print("✗ 项目不存在，请先创建项目")
        return 1

    print(f"  项目ID: {project.project_id}")
    print(f"  所有者: {project.owner}")
    print(f"  描述: {project.description}")
    print(f"  Agent列表: {', '.join(project.agents)}")

    # 获取项目工作空间路径
    workspace_dir = proj_mgr.get_project_workspace('chess_game')
    print(f"  工作空间: {workspace_dir}")

    # 步骤3: 创建任务
    print("\n步骤3: 创建开发任务...")
    from src.workflow.task import Task

    task = Task(
        task_id='chess_game_001',
        title='开发单机象棋游戏',
        description='''
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
    print(f"  标题: {task.title}")

    # 步骤4: 创建Agent实例
    print("\n步骤4: 创建Agent实例...")
    from src.agents.generic_agent import GenericAgent

    # 使用GenericAgent创建各个角色的Agent
    agents = []

    # Requester Agent
    requester_config = {
        'name': 'requester',
        'role': '需求分析师',
        'description': '分析和澄清需求',
        'system_prompt': '''你是需求分析师。分析用户需求，输出需求分析报告。
输出格式（JSON）：
{
    "analysis": "需求分析",
    "requirements": ["需求1", "需求2"],
    "feasibility": "可行性评估",
    "suggestions": ["建议1", "建议2"],
    "output": "分析结果",
    "next_agent": "product_manager"
}''',
        'tools': {'inherit_global': False, 'whitelist': []}
    }
    agents.append(GenericAgent(name='requester', config=requester_config))

    # Product Manager Agent
    pm_config = {
        'name': 'product_manager',
        'role': '产品经理',
        'description': '规划产品功能',
        'system_prompt': '''你是产品经理。规划功能，输出功能规划。
输出格式（JSON）：
{
    "features": [{"name": "功能名", "priority": "P0", "description": "描述"}],
    "milestones": ["M1: 里程碑1"],
    "output": "功能规划完成",
    "next_agent": "architect"
}''',
        'tools': {'inherit_global': False, 'whitelist': []}
    }
    agents.append(GenericAgent(name='product_manager', config=pm_config))

    # Architect Agent
    architect_config = {
        'name': 'architect',
        'role': '架构师',
        'description': '设计系统架构',
        'system_prompt': '''你是架构师。设计架构，输出架构设计。
输出格式（JSON）：
{
    "modules": [{"name": "模块名", "description": "描述"}],
    "class_design": {"类名": "描述"},
    "tech_stack": "技术栈",
    "output": "架构设计完成",
    "next_agent": "developer"
}''',
        'tools': {'inherit_global': False, 'whitelist': []}
    }
    agents.append(GenericAgent(name='architect', config=architect_config))

    # Developer Agent
    developer_config = {
        'name': 'developer',
        'role': '开发工程师',
        'description': '编写代码',
        'system_prompt': f'''你是开发工程师。根据架构设计编写代码。

重要：所有代码必须写入到工作空间目录：{workspace_dir}

使用MCP工具：
- mcp__filesystem__create_directory: 创建目录
- mcp__filesystem__write_file: 写入文件

输出格式（JSON）：
{{
    "files_created": ["文件1", "文件2"],
    "output": "代码编写完成",
    "next_agent": null
}}''',
        'tools': {
            'inherit_global': False,
            'whitelist': [
                'mcp__filesystem__write_file',
                'mcp__filesystem__create_directory',
                'mcp__filesystem__read_file',
                'mcp__filesystem__list_directory'
            ]
        }
    }
    agents.append(GenericAgent(name='developer', config=developer_config))

    print(f"✓ 创建了 {len(agents)} 个Agent:")
    for agent in agents:
        print(f"  - {agent.name} ({agent.role})")

    # 步骤5: 为Agent配置MCP工具
    print("\n步骤5: 为Agent配置MCP工具...")
    from src.registry.tool_registry import ToolRegistry

    # 注册MCP工具到全局注册表
    registry = ToolRegistry()
    for tool_name, tool in mcp_tools.items():
        if not registry.get(tool_name):
            metadata = {
                'name': tool_name,
                'display_name': tool.get_name(),
                'description': tool.get_description(),
                'type': 'mcp',
                'class_path': f'mcp.{tool.server_name}.{tool.tool_name}',
                'permission_level': tool.get_required_permission(),
                'dangerous': tool.is_dangerous(),
                'enabled': True,
                'tags': ['mcp', tool.server_name],
                'author': 'mcp',
                'mcp_server': tool.server_name,
                'mcp_tool': tool.tool_name
            }
            registry.register(tool_name, metadata)

    # 为Developer Agent添加文件操作工具
    developer = agents[3]  # DeveloperAgent
    file_tools = [
        'mcp__filesystem__write_file',
        'mcp__filesystem__create_directory',
        'mcp__filesystem__read_file',
        'mcp__filesystem__list_directory'
    ]

    added_count = 0
    for tool_name in file_tools:
        if tool_name in mcp_tools:
            tool = mcp_tools[tool_name]
            if hasattr(developer, 'tool_registry') and developer.tool_registry:
                developer.tool_registry.tools[tool_name] = tool
                added_count += 1

    print(f"✓ 为Developer添加了 {added_count} 个MCP工具")

    # 步骤6: 执行协作式工作流
    print("\n步骤6: 执行协作式工作流...")
    from src.workflow.collaborative_orchestrator import CollaborativeOrchestrator

    orchestrator = CollaborativeOrchestrator(
        agents=agents,
        max_iterations_per_agent=5,
        max_dispute_rounds=3
    )

    print("✓ Orchestrator创建成功")
    print(f"  最大迭代次数: 5")
    print(f"  最大争议轮次: 3")

    print("\n" + "="*60)
    print("开始执行工作流...")
    print("="*60)

    result = orchestrator.execute(task)

    # 步骤7: 输出结果
    print("\n" + "="*60)
    print("工作流执行结果")
    print("="*60)

    print(f"\n✅ 成功: {result['success']}")
    print(f"📊 最终状态: {result['final_status']}")
    print(f"💬 消息: {result['message']}")

    # 打印产物
    if task.artifacts:
        print(f"\n✓ 产物 (共{len(task.artifacts)}个):")
        for artifact in task.artifacts:
            print(f"  - {artifact.get('type')}: {artifact.get('agent')}")

    # 步骤8: 验证生成的文件
    print("\n步骤8: 验证生成的文件...")
    import os

    if workspace_dir.exists():
        files = list(workspace_dir.rglob('*.py'))
        print(f"✓ 工作空间存在: {workspace_dir}")
        print(f"  Python文件数: {len(files)}")
        for f in files:
            rel_path = f.relative_to(workspace_dir)
            print(f"    - {rel_path}")
    else:
        print(f"✗ 工作空间不存在: {workspace_dir}")

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
