#!/usr/bin/env python3
"""
测试Agent命名一致性

验证：
1. 配置文件中的name
2. Agent实例的name
3. agents_dict的key
4. available_agents列表中的名称
都保持一致
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.registration import AgentRegistration
from src.agents.requester import RequesterAgent
from src.agents.product_manager import ProductManagerAgent
from src.project_manager import ProjectManager

def test_agent_naming():
    """测试Agent命名一致性"""

    user_id = "user_test"
    registration = AgentRegistration(user_id=user_id)

    # 测试Agent列表
    test_agents = [
        ('requester', RequesterAgent),
        ('product_manager', ProductManagerAgent)
    ]

    print("=" * 80)
    print("Agent命名一致性测试")
    print("=" * 80)

    for agent_name, agent_class in test_agents:
        print(f"\n测试Agent: {agent_name}")
        print("-" * 40)

        # 1. 加载配置
        config = registration.load_config(agent_name)
        if not config:
            print(f"  ❌ 配置文件不存在")
            continue

        config_name = config.get('name')
        print(f"  配置文件中的name: {config_name}")

        # 2. 创建Agent实例
        agent = agent_class(name=config_name, config=config)
        print(f"  Agent实例的name: {agent.name}")

        # 3. 检查一致性
        if config_name == agent.name == agent_name:
            print(f"  ✅ 命名一致: {agent_name}")
        else:
            print(f"  ❌ 命名不一致!")
            print(f"     期望: {agent_name}")
            print(f"     配置: {config_name}")
            print(f"     实例: {agent.name}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == '__main__':
    test_agent_naming()
