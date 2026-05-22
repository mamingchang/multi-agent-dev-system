#!/usr/bin/env python3
"""
Multi-Agent系统 - 交互式项目创建工具

使用方式：
    python3 scripts/create_project_interactive.py

功能：
1. 创建新项目
2. 输入项目需求
3. 自动调用Agent团队开发
4. 生成可运行的代码
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')


def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(text)
    print("="*60)


def get_user_input(prompt, default=None):
    """获取用户输入"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("  ⚠️  输入不能为空，请重新输入")


def main():
    print("\n" + "🤖"*30)
    print("Multi-Agent系统 - 交互式项目创建")
    print("🤖"*30)

    # 步骤1: 获取用户信息
    print_header("步骤1: 用户信息")

    user_id = get_user_input("请输入用户ID", "user_test")
    print(f"  ✓ 用户ID: {user_id}")

    # 步骤2: 创建或选择项目
    print_header("步骤2: 项目设置")

    from src.project_manager import ProjectManager
    proj_mgr = ProjectManager(user_id=user_id)

    # 列出现有项目
    existing_projects = proj_mgr.list_projects()
    if existing_projects:
        print("\n现有项目:")
        for i, proj in enumerate(existing_projects, 1):
            print(f"  {i}. {proj.project_name} - {proj.description}")

    print("\n选项:")
    print("  1. 创建新项目")
    print("  2. 使用现有项目")

    choice = get_user_input("请选择", "1")

    if choice == "2" and existing_projects:
        # 使用现有项目
        proj_num = int(get_user_input(f"选择项目编号 (1-{len(existing_projects)})", "1"))
        project = existing_projects[proj_num - 1]
        print(f"  ✓ 使用项目: {project.project_name}")
    else:
        # 创建新项目
        project_name = get_user_input("项目名称（英文，如: my_app）")
        project_desc = get_user_input("项目描述（中文）")

        if proj_mgr.project_exists(project_name):
            print(f"  ⚠️  项目已存在: {project_name}")
            project = proj_mgr.get_project(project_name)
        else:
            project = proj_mgr.create_project(
                project_name=project_name,
                description=project_desc,
                agents=['requester', 'product_manager', 'architect', 'developer']
            )
            print(f"  ✓ 项目创建成功: {project_name}")

    workspace = proj_mgr.get_project_workspace(project.project_name)
    print(f"  ✓ 工作空间: {workspace}")

    # 步骤3: 输入开发需求
    print_header("步骤3: 开发需求")

    print("\n请描述你想开发的项目（可以多行输入，输入空行结束）:")
    print("示例:")
    print("  - 开发一个待办事项管理工具")
    print("  - 开发一个简单的计算器")
    print("  - 开发一个文件管理器")
    print()

    description_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        description_lines.append(line)

    if not description_lines:
        print("  ⚠️  未输入需求，使用默认示例")
        task_description = "开发一个简单的待办事项管理工具，支持添加、删除、标记完成任务。"
    else:
        task_description = "\n".join(description_lines)

    print(f"\n  ✓ 需求已记录")
    print(f"\n需求内容:")
    print("-"*60)
    print(task_description)
    print("-"*60)

    # 确认
    confirm = get_user_input("\n是否开始开发？(y/n)", "y")
    if confirm.lower() != 'y':
        print("\n  已取消")
        return 0

    # 步骤4: 初始化系统
    print_header("步骤4: 初始化系统")

    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools
    from src.workflow.task import Task
    from src.agents.generic_agent import GenericAgent
    from src.registry.tool_registry import ToolRegistry

    print("  启动MCP系统...")
    manager = MCPServerManager()
    manager.start_all_servers()
    mcp_tools = create_mcp_tools(manager)
    print(f"  ✓ MCP工具: {len(mcp_tools)}个")

    # 步骤5: 创建任务
    print_header("步骤5: 创建开发任务")

    task = Task(
        task_id=f'{project.project_name}_task_001',
        title=f'开发{project.project_name}',
        description=f'''{task_description}

技术要求：
- 使用Python 3.10+
- 代码清晰易懂
- 包含必要的注释

代码生成位置：{workspace}
'''
    )
    print(f"  ✓ 任务ID: {task.task_id}")

    # 步骤6: 创建Agent团队
    print_header("步骤6: 创建Agent团队")

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
}'''
        },
        {
            'name': 'product_manager',
            'role': '产品经理',
            'system_prompt': '''你是产品经理。规划功能，输出JSON格式：
{
    "features": [
        {"name": "功能名", "priority": "P0", "description": "描述（30字内）"}
    ],
    "milestones": ["M1: 里程碑1"],
    "output": "功能规划完成",
    "next_agent": "architect"
}'''
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
}'''
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

    # 步骤7: 执行工作流
    print_header("步骤7: 执行Agent工作流")
    print("\n⏳ 这可能需要几分钟，请耐心等待...\n")
    print("="*60)

    current_agent_name = 'requester'
    iteration = 0
    max_iterations = 10

    while current_agent_name and iteration < max_iterations:
        iteration += 1

        current_agent = None
        for agent in agents:
            if agent.name == current_agent_name:
                current_agent = agent
                break

        if not current_agent:
            print(f"\n✗ 找不到Agent: {current_agent_name}")
            break

        print(f"\n[{iteration}/4] {current_agent.name} ({current_agent.role})")
        print("-"*60)

        try:
            result = current_agent.process(task)

            if isinstance(result, dict):
                if 'output' in result:
                    output = result['output']
                    if isinstance(output, dict):
                        print(f"✓ {output.get('output', 'N/A')[:80]}")
                        current_agent_name = output.get('next_agent')
                    else:
                        print(f"✓ 完成")
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
            print("\n提示: 如果是API超时，可以稍后重试")
            break

    # 步骤8: 验证结果
    print("\n" + "="*60)
    print_header("步骤8: 验证结果")

    if workspace.exists():
        py_files = list(workspace.glob('*.py'))
        md_files = list(workspace.glob('*.md'))

        print(f"\n  ✓ 工作空间: {workspace}")
        print(f"  ✓ Python文件: {len(py_files)}个")
        for f in sorted(py_files):
            size = f.stat().st_size
            print(f"    - {f.name} ({size} bytes)")

        if md_files:
            print(f"  ✓ 文档文件: {len(md_files)}个")
            for f in md_files:
                print(f"    - {f.name}")

        # 测试代码
        if py_files:
            print("\n  测试代码语法...")
            import subprocess
            try:
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

    # 清理
    print("\n  清理资源...")
    manager.shutdown_all_servers()
    print("  ✓ MCP系统已关闭")

    # 总结
    print("\n" + "="*60)
    print("✅ 项目开发完成！")
    print("="*60)
    print(f"\n📁 项目位置: {workspace}")

    if workspace.exists():
        main_files = list(workspace.glob('main*.py'))
        if main_files:
            print(f"🚀 运行项目: cd {workspace} && python3 {main_files[0].name}")
        else:
            py_files = list(workspace.glob('*.py'))
            if py_files:
                print(f"🚀 运行项目: cd {workspace} && python3 {py_files[0].name}")

    print("\n💡 提示:")
    print("  - 查看生成的代码文件")
    print("  - 根据需要修改和完善")
    print("  - 运行测试验证功能")
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
