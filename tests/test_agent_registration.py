"""
Agent注册系统测试脚本

测试CapabilityLoader和AgentRegistration的核心功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.registration import AgentRegistration
from src.agents.capability_loader import CapabilityLoader


def test_registration_from_template():
    """测试从模板创建Agent"""
    print("\n=== 测试1：从模板创建Agent ===")

    registration = AgentRegistration()

    try:
        # 创建一个产品经理Agent
        config = registration.register_from_template(
            agent_name="pm_test",
            template_name="product_manager",
            overrides={
                "description": "测试用产品经理Agent"
            }
        )

        print(f"✓ 创建成功: {config['name']}")
        print(f"  角色: {config['role']}")
        print(f"  描述: {config['description']}")
        print(f"  版本: {config['metadata']['version']}")

        return True

    except Exception as e:
        print(f"✗ 创建失败: {e}")
        return False


def test_capability_loader():
    """测试CapabilityLoader加载能力"""
    print("\n=== 测试2：CapabilityLoader加载能力 ===")

    registration = AgentRegistration()

    try:
        # 加载刚创建的Agent配置
        config = registration.load_config("pm_test")

        # 创建CapabilityLoader
        loader = CapabilityLoader(config, project_root=project_root)

        # 加载工具
        tools = loader.load_tools()
        print(f"✓ 加载工具: {len(tools)}个")
        if tools:
            print(f"  工具列表: {list(tools.keys())[:5]}...")

        # 加载技能
        skills = loader.load_skills()
        print(f"✓ 加载技能: {len(skills)}个")
        if skills:
            print(f"  技能列表: {list(skills.keys())[:5]}...")

        # 加载插件
        plugins = loader.load_plugins()
        print(f"✓ 加载插件: {len(plugins)}个")

        # 加载MCP服务器
        mcp_servers = loader.load_mcp_servers()
        print(f"✓ 加载MCP服务器: {len(mcp_servers)}个")

        # 获取数据路径
        data_paths = loader.get_data_paths()
        print(f"✓ 数据路径:")
        print(f"  root: {data_paths['root']}")
        print(f"  memory: {data_paths['memory']}")
        print(f"  cache: {data_paths['cache']}")
        print(f"  logs: {data_paths['logs']}")

        return True

    except Exception as e:
        print(f"✗ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_agents():
    """测试列出所有Agent"""
    print("\n=== 测试3：列出所有Agent ===")

    registration = AgentRegistration()

    try:
        agents = registration.list_agents()
        print(f"✓ 找到 {len(agents)} 个Agent:")

        for agent in agents:
            print(f"  - {agent['name']} ({agent['role']})")
            print(f"    描述: {agent['description'][:50]}...")
            print(f"    版本: {agent['version']}")

        return True

    except Exception as e:
        print(f"✗ 列出失败: {e}")
        return False


def test_update_agent():
    """测试更新Agent配置"""
    print("\n=== 测试4：更新Agent配置 ===")

    registration = AgentRegistration()

    try:
        # 更新描述和LLM配置
        config = registration.update_config(
            "pm_test",
            {
                "description": "更新后的描述",
                "llm": {
                    "temperature": 0.9
                }
            }
        )

        print(f"✓ 更新成功")
        print(f"  新描述: {config['description']}")
        print(f"  新温度: {config['llm']['temperature']}")
        print(f"  新版本: {config['metadata']['version']}")

        return True

    except Exception as e:
        print(f"✗ 更新失败: {e}")
        return False


def test_register_from_existing():
    """测试从已有Agent复制"""
    print("\n=== 测试5：从已有Agent复制 ===")

    registration = AgentRegistration()

    try:
        # 从pm_test复制创建pm_test2
        config = registration.register_from_existing(
            source_agent="pm_test",
            new_agent_name="pm_test2",
            overrides={
                "description": "从pm_test复制的Agent"
            }
        )

        print(f"✓ 复制成功: {config['name']}")
        print(f"  源Agent: {config['metadata']['source_agent']}")
        print(f"  描述: {config['description']}")

        return True

    except Exception as e:
        print(f"✗ 复制失败: {e}")
        return False


def test_unregister_agent():
    """测试注销Agent"""
    print("\n=== 测试6：注销Agent ===")

    registration = AgentRegistration()

    try:
        # 注销测试Agent
        registration.unregister("pm_test", backup=True)
        print(f"✓ 注销 pm_test 成功")

        registration.unregister("pm_test2", backup=True)
        print(f"✓ 注销 pm_test2 成功")

        return True

    except Exception as e:
        print(f"✗ 注销失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Agent注册系统测试")
    print("=" * 60)

    tests = [
        test_registration_from_template,
        test_capability_loader,
        test_list_agents,
        test_update_agent,
        test_register_from_existing,
        test_unregister_agent
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"通过: {passed}/{total}")

    if passed == total:
        print("✓ 所有测试通过")
    else:
        print(f"✗ {total - passed} 个测试失败")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
