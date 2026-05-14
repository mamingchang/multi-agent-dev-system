"""
MVP测试脚本

测试简化的Agent工作流：
1. 创建任务
2. Requester分析需求
3. Developer开发
4. CodeReviewer审查
5. 支持多轮对话和反馈

使用Mock LLM，快速验证流程。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.workflow.task import Task
from src.conversation import Conversation
from src.agents.base_agent import BaseAgent
from src.llm.llm_client import create_llm_client, MockLLMAdapter
from src.conversation import MessageType
from typing import Dict, Any


# 创建简化的Requester Agent
class SimplifiedRequesterAgent(BaseAgent):
    """简化的Requester Agent - MVP版本"""

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
        """处理任务"""
        print(f"\n[{self.name}] 开始分析需求...")

        # 检查是否有反馈
        feedback = self._check_feedback(task)
        if feedback:
            print(f"[{self.name}] 收到反馈，正在修改...")

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)

            print(f"[{self.name}] 需求分析完成")
            print(f"\n{response}\n")

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


# 创建简化的Developer Agent
class SimplifiedDeveloperAgent(BaseAgent):
    """简化的Developer Agent - MVP版本"""

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
        return """请根据需求文档编写代码。

要求：
1. 代码要有完整的错误处理
2. 关键部分要有注释
3. 考虑边界情况

输出完整的代码。"""

    def process(self, task) -> Dict[str, Any]:
        """处理任务"""
        print(f"\n[{self.name}] 开始开发...")

        # 检查是否有反馈
        feedback = self._check_feedback(task)
        if feedback:
            print(f"[{self.name}] 收到反馈，正在修改代码...")
            # 发送确认消息
            self._send_message(
                task,
                feedback[0].from_agent,
                "收到反馈，正在修改",
                MessageType.INFO
            )

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)

            print(f"[{self.name}] 开发完成")
            print(f"\n{response}\n")

            return {
                'success': True,
                'output': response,
                'message': '开发完成'
            }

        except Exception as e:
            print(f"[{self.name}] 处理失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }


# 创建简化的CodeReviewer Agent
class SimplifiedCodeReviewerAgent(BaseAgent):
    """简化的CodeReviewer Agent - MVP版本"""

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
如果没有问题，请批准通过。"""

    def process(self, task) -> Dict[str, Any]:
        """处理任务"""
        print(f"\n[{self.name}] 开始审查代码...")

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)

            print(f"[{self.name}] 审查完成")
            print(f"\n{response}\n")

            # 简单判断：如果响应中包含"问题"或"修改"，则要求Developer修改
            if "问题" in response or "修改" in response:
                print(f"[{self.name}] 发现问题，要求Developer修改")

                # 发送修改请求
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

            else:
                print(f"[{self.name}] 代码通过审查")

                # 发送批准消息
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

        except Exception as e:
            print(f"[{self.name}] 处理失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }


def main():
    """主函数"""
    print("\n" + "="*60)
    print("MVP测试：简化的Agent工作流")
    print("="*60 + "\n")

    # 1. 创建Mock LLM客户端
    print("1. 创建Mock LLM客户端...")
    mock_responses = {
        "Requester": """# 需求分析文档

## 核心功能
- 用户登录功能
- 支持用户名/密码登录

## 技术要求
- 使用Python实现
- 密码需要加密存储

## 约束条件
- 简单实现，不需要复杂的认证机制

## 潜在风险
- 密码安全性
- SQL注入风险""",

        "Developer": """# 登录功能代码

```python
import hashlib

def login(username, password):
    # 密码加密
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # 查询数据库（简化版）
    # 这里应该使用参数化查询防止SQL注入
    user = db.query("SELECT * FROM users WHERE username=? AND password=?",
                    (username, hashed_password))

    if user:
        return {"success": True, "user": user}
    else:
        return {"success": False, "message": "用户名或密码错误"}
```

代码说明：
1. 使用SHA256加密密码
2. 使用参数化查询防止SQL注入
3. 返回明确的成功/失败信息""",

        "CodeReviewer": """# 代码审查结果

✅ 审查通过

优点：
1. 使用了密码加密（SHA256）
2. 使用了参数化查询防止SQL注入
3. 有清晰的返回值

建议：
- 可以考虑使用更安全的密码哈希算法（如bcrypt）
- 可以添加登录失败次数限制

总体质量良好，可以通过。"""
    }

    llm_client = create_llm_client("mock", responses=mock_responses)

    # 2. 创建Agent
    print("2. 创建Agent...")
    requester = SimplifiedRequesterAgent(llm_client)
    developer = SimplifiedDeveloperAgent(llm_client)
    code_reviewer = SimplifiedCodeReviewerAgent(llm_client)

    # 3. 创建任务
    print("3. 创建任务...")
    task = Task(
        task_id="task-001",
        title="实现用户登录功能",
        description="需要实现一个简单的用户登录功能，支持用户名和密码登录。"
    )

    # 4. 创建简化的Orchestrator
    print("4. 创建Orchestrator...")
    from src.workflow.simple_orchestrator import SimpleOrchestrator
    orchestrator = SimpleOrchestrator(
        agents=[requester, developer, code_reviewer],
        max_iterations=3
    )

    # 5. 执行工作流
    print("5. 执行工作流...\n")
    result = orchestrator.execute(task)

    # 6. 输出结果
    print("\n" + "="*60)
    print("执行结果")
    print("="*60)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    print(f"最终状态: {result['final_status']}")

    # 7. 输出对话历史
    if task.conversation:
        print("\n" + "="*60)
        print("对话历史")
        print("="*60)
        for msg in task.conversation.messages:
            print(f"\n[{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}")
            print(f"内容: {msg.content}")

    # 8. 输出产物
    print("\n" + "="*60)
    print("产物列表")
    print("="*60)
    for artifact in task.artifacts:
        print(f"\n类型: {artifact['type']}")
        print(f"Agent: {artifact['agent']}")
        print(f"版本: {artifact['version']}")
        print(f"内容预览: {artifact['content'][:100]}...")


if __name__ == "__main__":
    main()
