"""
LLM Client 测试脚本

演示如何使用LLM客户端系统
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm import LLMFactory, LLMConfig, get_config_loader


def test_direct_creation():
    """
    测试1：直接创建LLM客户端

    这种方式适合：
    - 临时测试
    - 不需要配置文件的场景
    """
    print("=" * 80)
    print("测试1：直接创建LLM客户端")
    print("=" * 80)

    # 检查环境变量
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量 ANTHROPIC_API_KEY")
        return

    # 创建配置
    config = LLMConfig(
        provider="claude",
        model="claude-3-sonnet-20240229",
        api_key=api_key,
        temperature=0.7,
        max_tokens=1024
    )

    # 通过工厂创建客户端
    client = LLMFactory.create(config)
    print(f"✓ 创建客户端成功: {client}")

    # 调用LLM
    try:
        print("\n发送请求: '你好，请用一句话介绍你自己'")
        response = client.call(
            prompt="你好，请用一句话介绍你自己",
            system_prompt="你是一个友好的AI助手"
        )

        print(f"\n✓ 响应成功:")
        print(f"  模型: {response.model}")
        print(f"  内容: {response.content}")
        print(f"  Token使用: {response.usage}")
        print(f"  完成原因: {response.finish_reason}")

    except Exception as e:
        print(f"❌ 调用失败: {str(e)}")


def test_config_file():
    """
    测试2：从配置文件加载

    这种方式适合：
    - 生产环境
    - 需要为不同Agent配置不同LLM的场景
    """
    print("\n" + "=" * 80)
    print("测试2：从配置文件加载")
    print("=" * 80)

    try:
        # 加载配置
        loader = get_config_loader()
        loader.load()

        # 获取Developer Agent的配置
        print("\n获取Developer Agent的配置...")
        dev_config = loader.get_agent_config("Developer")
        print(f"✓ 配置加载成功:")
        print(f"  Provider: {dev_config.provider}")
        print(f"  Model: {dev_config.model}")
        print(f"  Temperature: {dev_config.temperature}")
        print(f"  Max Tokens: {dev_config.max_tokens}")

        # 创建客户端
        if dev_config.api_key:
            client = LLMFactory.create(dev_config)
            print(f"✓ 创建客户端成功: {client}")
        else:
            print("⚠️  API密钥未配置，跳过客户端创建")

    except FileNotFoundError as e:
        print(f"❌ 配置文件不存在: {str(e)}")
    except Exception as e:
        print(f"❌ 加载配置失败: {str(e)}")


def test_multiple_providers():
    """
    测试3：多个提供商

    演示如何为不同Agent配置不同的LLM提供商
    """
    print("\n" + "=" * 80)
    print("测试3：多个提供商")
    print("=" * 80)

    try:
        loader = get_config_loader()
        loader.load()

        # 获取所有Agent的配置
        all_configs = loader.get_all_agent_configs()

        print(f"\n共配置了 {len(all_configs)} 个Agent:")
        for agent_name, config in all_configs.items():
            print(f"  - {agent_name:15s}: {config.provider:10s} / {config.model}")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


def test_factory_list():
    """
    测试4：列出支持的提供商
    """
    print("\n" + "=" * 80)
    print("测试4：支持的LLM提供商")
    print("=" * 80)

    providers = LLMFactory.list_providers()
    print(f"\n当前支持 {len(providers)} 个提供商:")
    for provider in providers:
        print(f"  - {provider}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           LLM Client System 测试                              ║
║                                                               ║
║  这个测试脚本演示了如何使用可配置的LLM客户端系统             ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 运行所有测试
    test_factory_list()
    test_config_file()
    test_multiple_providers()

    # 如果设置了API密钥，运行实际调用测试
    if os.getenv("ANTHROPIC_API_KEY"):
        test_direct_creation()
    else:
        print("\n" + "=" * 80)
        print("⚠️  跳过实际API调用测试（未设置ANTHROPIC_API_KEY）")
        print("=" * 80)

    print("\n" + "=" * 80)
    print("✓ 所有测试完成")
    print("=" * 80)
