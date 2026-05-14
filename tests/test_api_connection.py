"""
API连接测试工具

帮助配置和测试自定义API端点
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm import LLMFactory, LLMConfig


def test_api_connection(api_key: str, api_base: str = None, model: str = "claude-3-sonnet-20240229"):
    """
    测试API连接

    Args:
        api_key: API密钥
        api_base: API端点URL（可选）
        model: 模型名称
    """
    print("=" * 80)
    print("API连接测试")
    print("=" * 80)
    print(f"API密钥: {api_key[:20]}...{api_key[-10:]}")
    print(f"API端点: {api_base if api_base else '默认（官方API）'}")
    print(f"模型: {model}")
    print("=" * 80)

    try:
        # 创建配置
        config = LLMConfig(
            provider="claude",
            model=model,
            api_key=api_key,
            api_base=api_base,
            temperature=0.7,
            max_tokens=100  # 测试用，只生成少量token
        )

        # 创建客户端
        print("\n[1/3] 创建LLM客户端...")
        client = LLMFactory.create(config)
        print(f"✓ 客户端创建成功: {client}")

        # 发送测试请求
        print("\n[2/3] 发送测试请求...")
        print("提示词: '你好，请回复一个字：好'")

        response = client.call(
            prompt="你好，请回复一个字：好",
            system_prompt="你是一个测试助手，请严格按照用户要求回复。"
        )

        print(f"✓ 请求成功")

        # 显示结果
        print("\n[3/3] 响应结果:")
        print(f"  模型: {response.model}")
        print(f"  内容: {response.content}")
        print(f"  Token使用: {response.usage}")
        print(f"  完成原因: {response.finish_reason}")

        print("\n" + "=" * 80)
        print("✓ API连接测试成功！")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        print("\n" + "=" * 80)
        print("❌ API连接测试失败")
        print("=" * 80)

        # 提供调试建议
        print("\n调试建议:")
        print("1. 检查API密钥是否正确")
        print("2. 检查API端点URL是否正确（如果使用自定义端点）")
        print("3. 检查网络连接")
        print("4. 检查API服务是否兼容Anthropic格式")

        return False


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           API连接测试工具                                     ║
║                                                               ║
║  帮助你配置和测试自定义API端点                                ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 从环境变量读取配置
    api_key = os.getenv("ANTHROPIC_API_KEY")
    api_base = os.getenv("ANTHROPIC_API_BASE")

    if not api_key:
        print("❌ 错误: 未设置ANTHROPIC_API_KEY环境变量")
        print("\n使用方法:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("  export ANTHROPIC_API_BASE='https://api.example.com/v1'  # 可选")
        print("  python3 tests/test_api_connection.py")
        sys.exit(1)

    # 运行测试
    success = test_api_connection(api_key, api_base)

    sys.exit(0 if success else 1)
