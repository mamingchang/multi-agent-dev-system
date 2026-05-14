"""
详细的API调试工具

获取完整的错误信息和请求详情
"""

import os
import sys
import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def debug_api_call():
    """详细调试API调用"""

    # 使用Claude Code相同的token
    api_key = "sk-c52f339980aa7b41ff288fdf430410ffd90163e9ba7b638ca72b2559a42234da"
    api_base = "https://plan.zetarouter.com"

    print("=" * 80)
    print("详细API调试")
    print("=" * 80)
    print(f"API端点: {api_base}")
    print(f"API密钥: {api_key[:20]}...{api_key[-10:]}")
    print("=" * 80)

    try:
        # 创建客户端
        print("\n[1] 创建Anthropic客户端...")
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=api_base,
            timeout=60.0
        )
        print("✓ 客户端创建成功")

        # 发送请求
        print("\n[2] 发送API请求...")
        print("请求参数:")
        print(f"  model: claude-3-5-sonnet-20241022")  # 使用最新模型
        print(f"  max_tokens: 100")
        print(f"  messages: [user: '你好']")

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 使用最新模型
            max_tokens=100,
            messages=[
                {"role": "user", "content": "你好"}
            ]
        )

        print("\n✓ 请求成功!")
        print(f"响应: {response.content[0].text}")

    except anthropic.APIError as e:
        print(f"\n✗ API错误:")
        print(f"  类型: {type(e).__name__}")
        print(f"  消息: {str(e)}")
        print(f"  状态码: {getattr(e, 'status_code', 'N/A')}")
        print(f"  响应: {getattr(e, 'response', 'N/A')}")

        # 尝试获取更多信息
        if hasattr(e, 'body'):
            print(f"  响应体: {e.body}")

    except Exception as e:
        print(f"\n✗ 未知错误:")
        print(f"  类型: {type(e).__name__}")
        print(f"  消息: {str(e)}")


if __name__ == "__main__":
    debug_api_call()
