"""
使用真实Claude API测试

测试场景：
1. 使用Claude API替代Mock
2. 测试真实的Agent对话
3. 验证LLM能否理解角色和任务

注意：
- 需要设置ANTHROPIC_API_KEY环境变量
- 会消耗真实的Token
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.workflow.task import Task
from src.agents.base_agent import BaseAgent
from src.llm.llm_client import create_llm_client
from src.conversation import MessageType
from src.workflow.simple_orchestrator import SimpleOrchestrator
from typing import Dict, Any


# 复用之前的Agent类
class SimplifiedRequesterAgent(BaseAgent):
    """简化的Requester Agent"""

    def __init__(self, llm_client):
        super().__init__("Requester", "需求分析师", llm_client=llm_client)
        self.principles = [
            "需求必须清晰明确",
            "不能遗漏关键信息",
            "必须考虑可行性"
        ]

    def _get_responsibilities(self) -> str:
        return """1. 分析用户需求的完整性
2. 识别需求中的关键点
3. 提出澄清问题（如果需要）
4. 输出结构化的需求文档"""

    def _get_task_instruction(self, task) -> str:
        return """请分析这个需求，输出结构化的需求文档，包括：
1. 核心功能
2. 技术要求
3. 约束条件
4. 潜在风险

输出格式为Markdown。"""

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 开始分析需求...")

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)

            print(f"[{self.name}] 需求分析完成")
            print(f"\n--- Requester输出 ---")
            print(response)
            print(f"--- 输出结束 ---\n")

            return {
                'success': True,
                'output': response,
                'message': '需求分析完成'
            }

        except Exception as e:
            print(f"[{self.name}] 处理失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }


class SimplifiedDeveloperAgent(BaseAgent):
    """简化的Developer Agent"""

    def __init__(self, llm_client):
        super().__init__("Developer", "开发工程师", llm_client=llm_client)
        self.principles = [
            "代码必须有错误处理",
            "代码必须有注释",
            "不能有明显的Bug"
        ]

    def _get_responsibilities(self) -> str:
        return """1. 根据需求文档编写代码
2. 确保代码质量
3. 添加必要的注释
4. 处理边界情况"""

    def _get_task_instruction(self, task) -> str:
        feedback = self._check_feedback(task)
        if feedback:
            return """你收到了反馈，请根据反馈修改代码。

要求：
1. 仔细阅读反馈意见
2. 修改代码中的问题
3. 确保所有问题都已解决

输出修改后的完整代码。"""
        else:
            return """请根据需求文档编写代码。

要求：
1. 代码要有完整的错误处理
2. 关键部分要有注释
3. 考虑边界情况

输出完整的代码，使用代码块格式。"""

    def process(self, task) -> Dict[str, Any]:
        feedback = self._check_feedback(task)

        if feedback:
            print(f"\n[{self.name}] 收到反馈，正在修改代码...")
            self._send_message(
                task,
                feedback[0].from_agent,
                "收到反馈，正在修改",
                MessageType.INFO
            )
        else:
            print(f"\n[{self.name}] 开始开发...")

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)

            iteration = task.get_iteration_count(self.name) + 1
            print(f"[{self.name}] 开发完成（第{iteration}次迭代）")
            print(f"\n--- Developer输出 ---")
            print(response[:500] + "..." if len(response) > 500 else response)
            print(f"--- 输出结束 ---\n")

            return {
                'success': True,
                'output': response,
                'message': f'开发完成（第{iteration}次迭代）'
            }

        except Exception as e:
            print(f"[{self.name}] 处理失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }


class SimplifiedCodeReviewerAgent(BaseAgent):
    """简化的CodeReviewer Agent"""

    def __init__(self, llm_client):
        super().__init__("CodeReviewer", "代码审查员", llm_client=llm_client)
        self.principles = [
            "代码规范不能妥协",
            "安全问题必须修复",
            "错误处理必须完整"
        ]

    def _get_responsibilities(self) -> str:
        return """1. 审查代码质量
2. 检查错误处理
3. 验证代码规范
4. 提出改进建议"""

    def _get_task_instruction(self, task) -> str:
        return """请审查代码，检查：
1. 是否有错误处理
2. 是否有注释
3. 是否有明显Bug
4. 代码规范是否符合要求

如果有问题，请明确指出并要求修改。
如果没有问题，请明确说"审查通过"。"""

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 开始审查代码...")

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)

            print(f"[{self.name}] 审查完成")
            print(f"\n--- CodeReviewer输出 ---")
            print(response)
            print(f"--- 输出结束 ---\n")

            # 判断：如果响应中包含"通过"，则通过
            if "通过" in response or "PASS" in response.upper():
                print(f"[{self.name}] ✅ 代码通过审查")

                self._send_message(
                    task,
                    "Developer",
                    "代码审查通过",
                    MessageType.APPROVAL
                )

                return {
                    'success': True,
                    'output': response,
                    'message': '代码审查通过'
                }

            else:
                print(f"[{self.name}] ❌ 发现问题，要求Developer修改")

                self._send_message(
                    task,
                    "Developer",
                    response,
                    MessageType.REVISION_REQUEST
                )

                return {
                    'success': False,
                    'message': '代码需要修改',
                    'action': 'revise',
                    'next_agent': 'Developer'
                }

        except Exception as e:
            print(f"[{self.name}] 处理失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }


def main():
    """主函数"""
    print("\n" + "="*60)
    print("测试：使用真实Claude API")
    print("="*60 + "\n")

    # 1. 检查API密钥
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        print("❌ 错误：未设置ANTHROPIC_API_KEY或ANTHROPIC_AUTH_TOKEN环境变量")
        print("\n请设置环境变量：")
        print("export ANTHROPIC_API_KEY='your-api-key'")
        print("或")
        print("export ANTHROPIC_AUTH_TOKEN='your-api-key'")
        return

    print(f"✅ API密钥已设置（前10位）: {api_key[:10]}...\n")

    # 2. 创建Claude LLM客户端
    print("1. 创建Claude LLM客户端...")
    try:
        llm_client = create_llm_client(
            "claude",
            api_key=api_key,
            model="claude-sonnet-4-6"
        )
        print("✅ Claude客户端创建成功\n")
    except Exception as e:
        print(f"❌ 创建失败: {str(e)}")
        return

    # 3. 创建Agent
    print("2. 创建Agent...\n")
    requester = SimplifiedRequesterAgent(llm_client)
    developer = SimplifiedDeveloperAgent(llm_client)
    code_reviewer = SimplifiedCodeReviewerAgent(llm_client)

    # 4. 创建任务
    print("3. 创建任务...\n")
    task = Task(
        task_id="task-claude-001",
        title="实现简单的计算器",
        description="实现一个简单的计算器，支持加减乘除四则运算。要求：使用Python实现，有错误处理，有单元测试。"
    )

    # 5. 创建Orchestrator
    print("4. 创建Orchestrator...\n")
    orchestrator = SimpleOrchestrator(
        agents=[requester, developer, code_reviewer],
        max_iterations=3
    )

    # 6. 执行工作流
    print("5. 执行工作流...\n")
    print("⚠️  注意：这将调用真实的Claude API，会消耗Token\n")

    try:
        result = orchestrator.execute(task)

        # 7. 输出结果
        print("\n" + "="*60)
        print("执行结果")
        print("="*60)
        print(f"成功: {result['success']}")
        print(f"消息: {result['message']}")
        print(f"最终状态: {result['final_status']}")

        # 8. 输出统计
        print("\n" + "="*60)
        print("执行统计")
        print("="*60)
        for agent_name, count in task.iteration_count.items():
            print(f"{agent_name}: {count}次")

        # 9. 输出产物数量
        print("\n" + "="*60)
        print("产物统计")
        print("="*60)
        print(f"总产物数: {len(task.artifacts)}")
        for artifact in task.artifacts:
            print(f"- [{artifact['agent']}] {artifact['type']} (v{artifact['version']})")

    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
