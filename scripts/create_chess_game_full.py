#!/usr/bin/env python3
"""
完整的象棋游戏开发工作流

使用Multi-Agent系统完成：
1. Requester - 需求分析
2. Product Manager - 功能规划
3. Architect - 架构设计
4. Developer - 代码实现
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')


def main():
    print("\n" + "🎮"*30)
    print("Multi-Agent系统 - 开发单机象棋游戏")
    print("🎮"*30)

    # 步骤1: 初始化
    print("\n[1/6] 初始化系统...")
    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools
    from src.project_manager import ProjectManager
    from src.workflow.task import Task
    from src.agents.generic_agent import GenericAgent
    from src.registry.tool_registry import ToolRegistry

    manager = MCPServerManager()
    manager.start_all_servers()
    mcp_tools = create_mcp_tools(manager)

    proj_mgr = ProjectManager(user_id='user_test')
    project = proj_mgr.get_project('chess_game')
    workspace = proj_mgr.get_project_workspace('chess_game')

    print(f"  ✓ MCP工具: {len(mcp_tools)}个")
    print(f"  ✓ 项目: {project.project_id}")
    print(f"  ✓ 工作空间: {workspace}")

    # 步骤2: 创建任务
    print("\n[2/6] 创建开发任务...")
    task = Task(
        task_id='chess_full_workflow',
        title='开发单机象棋游戏',
        description=f'''开发一个简单的单机象棋游戏。

功能需求：
1. 基本的象棋规则（将、士、象、马、车、炮、兵）
2. 10x9棋盘显示
3. 红黑双方轮流走棋
4. 基本的走棋规则验证
5. 简单的AI对手（随机走棋）
6. 胜负判断

技术要求：
- Python 3.10+
- 命令行界面
- 代码清晰易懂

代码生成位置：{workspace}
'''
    )
    print(f"  ✓ 任务ID: {task.task_id}")

    # 步骤3: 创建Agent
    print("\n[3/6] 创建Agent团队...")

    agents_config = [
        {
            'name': 'requester',
            'role': '需求分析师',
            'system_prompt': '''你是需求分析师。分析需求，输出JSON格式：
{
    "analysis": "需求分析（50字内）",
    "requirements": ["需求1", "需求2", "需求3"],
    "feasibility": "可行性评估（30字内）",
    "suggestions": ["建议1", "建议2"],
    "output": "分析完成（30字内）",
    "next_agent": "product_manager"
}

要求：简洁明了，每项不超过50字。'''
        },
        {
            'name': 'product_manager',
            'role': '产品经理',
            'system_prompt': '''你是产品经理。规划功能，输出JSON格式：
{
    "features": [
        {"name": "功能名", "priority": "P0", "description": "描述（30字内）"}
    ],
    "milestones": ["M1: 里程碑1", "M2: 里程碑2"],
    "output": "功能规划完成",
    "next_agent": "architect"
}

要求：3-5个核心功能，简洁明了。'''
        },
        {
            'name': 'architect',
            'role': '架构师',
            'system_prompt': '''你是架构师。设计架构，输出JSON格式：
{
    "modules": [
        {"name": "文件名.py", "description": "模块描述（30字内）"}
    ],
    "class_design": {"类名": "职责描述"},
    "tech_stack": "Python 3.10+",
    "output": "架构设计完成",
    "next_agent": "developer"
}

要求：4-6个核心模块，清晰的类设计。'''
        },
        {
            'name': 'developer',
            'role': '开发工程师',
            'system_prompt': f'''你是开发工程师。编写代码。

重要：
1. 根据架构设计编写完整的Python代码
2. 代码要能直接运行
3. 包含必要的注释
4. 使用MCP工具将代码写入文件

可用工具：
- mcp__filesystem__write_file: 写入文件
- mcp__filesystem__create_directory: 创建目录

工作空间：{workspace}

输出JSON格式：
{{
    "files_created": ["文件1.py", "文件2.py"],
    "output": "代码编写完成，已生成N个文件",
    "next_agent": null
}}

注意：必须使用工具写入文件到工作空间！'''
        }
    ]

    agents = []
    for config in agents_config:
        agent_config = {
            **config,
            'llm': {'provider': 'claude', 'model': 'claude-sonnet-4-5'},
            'tools': {'inherit_global': False, 'whitelist': []}
        }
        agent = GenericAgent(name=config['name'], config=agent_config)
        agents.append(agent)

    print(f"  ✓ 创建了{len(agents)}个Agent")
    for agent in agents:
        print(f"    - {agent.name} ({agent.role})")

    # 为Developer添加MCP工具
    developer = agents[3]
    registry = ToolRegistry()
    for tool_name, tool in mcp_tools.items():
        if not registry.get(tool_name):
            registry.register(tool_name, {'name': tool_name, 'type': 'mcp', 'enabled': True})

    file_tools = ['mcp__filesystem__write_file', 'mcp__filesystem__create_directory']
    for tool_name in file_tools:
        if tool_name in mcp_tools and hasattr(developer, 'tool_registry'):
            developer.tool_registry.tools[tool_name] = mcp_tools[tool_name]

    print(f"  ✓ Developer配置了{len(file_tools)}个MCP工具")

    # 步骤4: 执行工作流
    print("\n[4/6] 执行Agent工作流...")
    print("="*60)

    current_agent_name = 'requester'
    iteration = 0
    max_iterations = 10

    while current_agent_name and iteration < max_iterations:
        iteration += 1

        # 找到当前Agent
        current_agent = None
        for agent in agents:
            if agent.name == current_agent_name:
                current_agent = agent
                break

        if not current_agent:
            print(f"\n✗ 找不到Agent: {current_agent_name}")
            break

        print(f"\n[迭代 {iteration}] {current_agent.name} ({current_agent.role})")
        print("-"*60)

        try:
            result = current_agent.process(task)

            if isinstance(result, dict):
                if 'output' in result:
                    output = result['output']
                    if isinstance(output, dict):
                        print(f"✓ 输出: {output.get('output', 'N/A')}")
                        current_agent_name = output.get('next_agent')
                    else:
                        print(f"✓ 输出: {str(output)[:100]}")
                        current_agent_name = result.get('next_agent')
                else:
                    print(f"✓ 完成")
                    current_agent_name = result.get('next_agent')
            else:
                print(f"✓ 完成")
                current_agent_name = None

            if current_agent_name:
                print(f"→ 下一个: {current_agent_name}")
            else:
                print("→ 工作流结束")
                break

        except Exception as e:
            print(f"✗ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            break

    # 步骤5: 验证结果
    print("\n" + "="*60)
    print("[5/6] 验证生成的代码...")

    if workspace.exists():
        py_files = list(workspace.glob('*.py'))
        md_files = list(workspace.glob('*.md'))

        print(f"  ✓ 工作空间: {workspace}")
        print(f"  ✓ Python文件: {len(py_files)}个")
        for f in sorted(py_files):
            size = f.stat().st_size
            print(f"    - {f.name} ({size} bytes)")

        if md_files:
            print(f"  ✓ 文档文件: {len(md_files)}个")
            for f in md_files:
                print(f"    - {f.name}")

        # 测试导入
        if py_files:
            print("\n  测试代码...")
            import subprocess
            try:
                # 尝试导入主模块
                main_files = [f for f in py_files if 'main' in f.name.lower()]
                if main_files:
                    result = subprocess.run(
                        ['python3', '-m', 'py_compile', str(main_files[0])],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        print(f"  ✓ 代码语法正确")
                    else:
                        print(f"  ⚠️  语法检查: {result.stderr[:100]}")
            except Exception as e:
                print(f"  ⚠️  测试失败: {e}")
    else:
        print(f"  ✗ 工作空间不存在")

    # 步骤6: 清理
    print("\n[6/6] 清理资源...")
    manager.shutdown_all_servers()
    print("  ✓ MCP系统已关闭")

    # 总结
    print("\n" + "="*60)
    print("✓ 象棋游戏开发完成！")
    print("="*60)
    print(f"\n📁 项目位置: {workspace}")
    if workspace.exists() and list(workspace.glob('main*.py')):
        print(f"🎮 运行游戏: cd {workspace} && python3 main.py")
    print()

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
