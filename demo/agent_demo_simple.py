#!/usr/bin/env python3
"""
Agent协作演示 - 简化版（不调用LLM）

演示Agent注册系统和工作流，使用模拟输出
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.registration import AgentRegistration


def demo_agent_system():
    """演示Agent注册系统"""
    print("=" * 80)
    print("Agent注册系统演示")
    print("=" * 80)
    print()

    registration = AgentRegistration()

    # 1. 列出所有Agent
    print("1. 已注册的Agent:")
    print("-" * 80)
    agents = registration.list_agents()
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent['name']} ({agent['role']})")
        print(f"   描述: {agent['description']}")
        print(f"   版本: {agent['version']}")
        print()

    # 2. 查看某个Agent的详细配置
    print("\n2. Developer Agent详细配置:")
    print("-" * 80)
    config = registration.load_config('developer')
    print(f"名称: {config['name']}")
    print(f"角色: {config['role']}")
    print(f"描述: {config['description']}")
    print(f"\nLLM配置:")
    print(f"  提供商: {config['llm']['provider']}")
    print(f"  模型: {config['llm']['model']}")
    print(f"  温度: {config['llm']['temperature']}")
    print(f"  最大Token: {config['llm']['max_tokens']}")
    print(f"\n工具配置:")
    print(f"  继承全局: {config['tools']['inherit_global']}")
    print(f"  黑名单: {config['tools']['blacklist']}")
    print(f"\n协作配置:")
    print(f"  可协作角色: {', '.join(config['collaboration']['can_collaborate_with'])}")
    print(f"  输出格式: {config['collaboration']['output_format']}")

    # 3. 使用CapabilityLoader加载能力
    print("\n\n3. 使用CapabilityLoader加载Developer的能力:")
    print("-" * 80)
    from src.agents.capability_loader import CapabilityLoader

    loader = CapabilityLoader(config)
    tools = loader.load_tools()
    skills = loader.load_skills()
    plugins = loader.load_plugins()
    mcp_servers = loader.load_mcp_servers()
    data_paths = loader.get_data_paths()

    print(f"工具: {len(tools)}个")
    print(f"技能: {len(skills)}个")
    print(f"插件: {len(plugins)}个")
    print(f"MCP服务器: {len(mcp_servers)}个")
    print(f"\n数据路径:")
    for key, path in data_paths.items():
        print(f"  {key}: {path}")

    # 4. 演示工作流顺序
    print("\n\n4. 完整开发工作流:")
    print("-" * 80)
    workflow = [
        ('requester', '需求收集和澄清'),
        ('product_manager', '需求分析和产品设计'),
        ('architect', '系统架构设计和技术选型'),
        ('developer', '代码实现和单元测试'),
        ('code_reviewer', '代码质量检查'),
        ('tester', '测试用例设计和执行'),
        ('devops', '部署和运维')
    ]

    for i, (name, desc) in enumerate(workflow, 1):
        config = registration.load_config(name)
        print(f"{i}. {config['name']} ({config['role']})")
        print(f"   职责: {desc}")
        print(f"   温度: {config['llm']['temperature']} (创造性: {'高' if config['llm']['temperature'] > 0.6 else '中' if config['llm']['temperature'] > 0.4 else '低'})")
        print()

    # 5. 演示Agent管理操作
    print("\n5. Agent管理操作示例:")
    print("-" * 80)
    print("# 查看所有Agent")
    print("./mas agent list")
    print()
    print("# 查看某个Agent的配置")
    print("./mas agent show developer")
    print()
    print("# 更新Agent配置")
    print("./mas agent update developer --set llm.temperature=0.5")
    print()
    print("# 从已有Agent复制创建新Agent")
    print("./mas agent register --method existing --name developer2 --source developer")
    print()
    print("# 注销Agent")
    print("./mas agent unregister developer2")

    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)


if __name__ == '__main__':
    try:
        demo_agent_system()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
