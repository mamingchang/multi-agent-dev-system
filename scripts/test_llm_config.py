#!/usr/bin/env python3
"""
测试启用LLM的Agent

验证LLM配置是否正确加载和工作
"""

import sys
from pathlib import Path
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_llm_config():
    """测试LLM配置加载"""
    print("\n" + "="*60)
    print("测试1: LLM配置加载")
    print("="*60)

    from src.llm import get_config_loader

    loader = get_config_loader()

    try:
        config_data = loader.load()
        print("✓ 配置文件加载成功")

        # 显示默认配置
        default = config_data.get('default', {})
        print(f"\n默认配置:")
        print(f"  Provider: {default.get('provider')}")
        print(f"  Model: {default.get('model')}")
        print(f"  API Base: {default.get('api_base')}")
        print(f"  Temperature: {default.get('temperature')}")
        print(f"  Max Tokens: {default.get('max_tokens')}")

        # 显示API密钥状态
        api_keys = config_data.get('api_keys', {})
        print(f"\nAPI密钥配置:")
        for provider, key in api_keys.items():
            if key:
                print(f"  {provider}: {'已设置' if key else '未设置'} ({key[:20]}...)" if len(key) > 20 else f"  {provider}: {key}")
            else:
                print(f"  {provider}: 未设置")

        # 显示Agent配置
        agents = config_data.get('agents', {})
        print(f"\nAgent配置数量: {len(agents)}")
        for agent_name in list(agents.keys())[:3]:
            print(f"  - {agent_name}")

        return True

    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_client():
    """测试LLM客户端创建"""
    print("\n" + "="*60)
    print("测试2: LLM客户端创建")
    print("="*60)

    from src.llm import LLMFactory, get_config_loader

    loader = get_config_loader()

    try:
        # 获取Developer的配置
        config = loader.get_agent_config('Developer')
        print(f"✓ 获取Developer配置成功")
        print(f"  Provider: {config.provider}")
        print(f"  Model: {config.model}")
        print(f"  API Key: {'已设置' if config.api_key else '未设置'}")

        # 创建LLM客户端
        client = LLMFactory.create(config)
        print(f"✓ LLM客户端创建成功: {type(client).__name__}")

        return True

    except Exception as e:
        print(f"✗ LLM客户端创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_with_llm():
    """测试带LLM的Agent"""
    print("\n" + "="*60)
    print("测试3: 创建带LLM的Agent")
    print("="*60)

    from src.agents.generic_agent import GenericAgent

    # 创建Developer Agent配置
    developer_config = {
        'name': 'developer',
        'role': '开发工程师',
        'description': '编写高质量代码',
        'system_prompt': '''你是一个专业的开发工程师。

你的职责：
1. 根据架构设计编写代码
2. 确保代码质量和可维护性
3. 编写清晰的注释

输出格式（JSON）：
{
    "analysis": "任务分析",
    "code_files": ["文件1", "文件2"],
    "output": "代码编写完成",
    "next_agent": null
}''',
        'llm': {
            'provider': 'claude',
            'model': 'claude-sonnet-4-5'
        },
        'tools': {
            'inherit_global': False,
            'whitelist': []
        }
    }

    try:
        agent = GenericAgent(name='developer', config=developer_config)
        print(f"✓ Agent创建成功")
        print(f"  名称: {agent.name}")
        print(f"  角色: {agent.role}")
        print(f"  LLM客户端: {'已配置' if agent.llm_client else '未配置'}")

        return True

    except Exception as e:
        print(f"✗ Agent创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_llm_call():
    """测试简单的LLM调用"""
    print("\n" + "="*60)
    print("测试4: 简单LLM调用")
    print("="*60)

    from src.llm.llm_client import ClaudeLLMAdapter

    try:
        # 创建Claude客户端
        client = ClaudeLLMAdapter(model='claude-sonnet-4-5')
        print(f"✓ Claude客户端创建成功")

        # 测试调用
        print("\n发送测试请求...")
        response = client.chat(
            system="你是一个友好的助手。",
            user="请用一句话介绍你自己。",
            max_tokens=100
        )

        print(f"✓ LLM调用成功")
        print(f"\n响应内容:")
        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")

        return True

    except Exception as e:
        print(f"✗ LLM调用失败: {e}")
        print(f"\n错误详情:")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "🧪"*30)
    print("LLM配置测试")
    print("🧪"*30)

    results = []

    # 测试1: 配置加载
    results.append(("配置加载", test_llm_config()))

    # 测试2: LLM客户端创建
    results.append(("LLM客户端创建", test_llm_client()))

    # 测试3: Agent创建
    results.append(("Agent创建", test_agent_with_llm()))

    # 测试4: LLM调用（可选，需要有效的API）
    print("\n是否测试实际的LLM调用？（需要有效的API密钥）")
    print("输入 'y' 继续，其他键跳过: ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            results.append(("LLM调用", test_simple_llm_call()))
    except:
        print("跳过LLM调用测试")

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n通过: {passed}/{total}")
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    if passed == total:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
