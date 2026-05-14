"""
测试多轮对话和反馈循环

场景：
1. Requester分析需求
2. Developer开发（故意写有问题的代码）
3. CodeReviewer发现问题，要求修改
4. Developer修改代码
5. CodeReviewer再次审查，通过

验证：
- 反馈循环是否正常工作
- Developer是否能看到反馈
- 迭代次数是否正确记录
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


# 复用之前的SimplifiedRequesterAgent
class SimplifiedRequesterAgent(BaseAgent):
    """简化的Requester Agent"""

    def __init__(self, llm_client):
        super().__init__("Requester", "需求分析师", llm_client=llm_client)
        self.principles = ["需求必须清晰明确", "不能遗漏关键信息"]

    def _get_responsibilities(self) -> str:
        return "分析用户需求，输出结构化的需求文档"

    def _get_task_instruction(self, task) -> str:
        return "请分析需求并输出结构化文档。"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 开始分析需求...")
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)
        response = self._call_llm(system_prompt, user_prompt)
        print(f"[{self.name}] 需求分析完成\n")
        return {'success': True, 'output': response, 'message': '需求分析完成'}


# Developer Agent - 支持反馈修改
class SimplifiedDeveloperAgent(BaseAgent):
    """简化的Developer Agent - 支持多轮修改"""

    def __init__(self, llm_client):
        super().__init__("Developer", "开发工程师", llm_client=llm_client)
        self.principles = ["代码必须有错误处理", "代码必须有注释"]

    def _get_responsibilities(self) -> str:
        return "根据需求编写高质量代码"

    def _get_task_instruction(self, task) -> str:
        # 检查是否有反馈
        feedback = self._check_feedback(task)
        if feedback:
            return """你收到了CodeReviewer的反馈，请根据反馈修改代码。

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

输出完整的代码。"""

    def process(self, task) -> Dict[str, Any]:
        # 检查是否有反馈
        feedback = self._check_feedback(task)

        if feedback:
            print(f"\n[{self.name}] 收到反馈，正在修改代码...")
            print(f"[{self.name}] 反馈内容: {feedback[0].content[:100]}...")

            # 发送确认消息
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
        response = self._call_llm(system_prompt, user_prompt)

        iteration = task.get_iteration_count(self.name) + 1
        print(f"[{self.name}] 开发完成（第{iteration}次迭代）\n")

        return {
            'success': True,
            'output': response,
            'message': f'开发完成（第{iteration}次迭代）'
        }


# CodeReviewer Agent - 第一次发现问题，第二次通过
class SimplifiedCodeReviewerAgent(BaseAgent):
    """简化的CodeReviewer Agent - 支持多轮审查"""

    def __init__(self, llm_client):
        super().__init__("CodeReviewer", "代码审查员", llm_client=llm_client)
        self.principles = ["代码规范不能妥协", "错误处理必须完整"]

    def _get_responsibilities(self) -> str:
        return "审查代码质量，确保符合规范"

    def _get_task_instruction(self, task) -> str:
        iteration = task.get_iteration_count("Developer")

        if iteration == 1:
            # 第一次审查：要求严格
            return """请严格审查代码，检查：
1. 是否有完整的错误处理
2. 是否有足够的注释
3. 是否有明显Bug
4. 代码规范是否符合要求

如果有任何问题，请明确指出并要求修改。"""
        else:
            # 第二次审查：检查是否修改
            return """这是Developer修改后的代码，请检查：
1. 之前提出的问题是否已解决
2. 修改是否正确
3. 是否引入新问题

如果问题已解决，请批准通过。"""

    def process(self, task) -> Dict[str, Any]:
        developer_iteration = task.get_iteration_count("Developer")
        print(f"\n[{self.name}] 开始审查代码（Developer第{developer_iteration}次迭代）...")

        # 构建Prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        response = self._call_llm(system_prompt, user_prompt)

        print(f"[{self.name}] 审查完成\n")

        # 判断是否通过
        # 第一次审查：发现问题
        # 第二次审查：通过
        if developer_iteration == 1:
            print(f"[{self.name}] ❌ 发现问题，要求Developer修改\n")

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
            print(f"[{self.name}] ✅ 代码通过审查\n")

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


def main():
    """主函数"""
    print("\n" + "="*60)
    print("测试：多轮对话和反馈循环")
    print("="*60 + "\n")

    # 1. 创建Mock LLM客户端
    print("1. 创建Mock LLM客户端...\n")
    mock_responses = {
        "Requester": """# 需求分析文档

## 核心功能
- 实现文件上传功能
- 支持多种文件格式

## 技术要求
- 使用Python实现
- 需要验证文件类型和大小

## 约束条件
- 文件大小限制10MB
- 只支持图片和文档格式""",

        "Developer": """# 文件上传代码（第1版 - 有问题）

```python
def upload_file(file):
    # 保存文件
    file.save('/uploads/' + file.filename)
    return {"success": True}
```

说明：实现了基本的文件上传功能。""",

        "CodeReviewer": """# 代码审查结果（第1次）

❌ 发现以下问题：

1. **缺少文件类型验证** - 没有检查文件格式
2. **缺少文件大小验证** - 没有限制文件大小
3. **缺少错误处理** - 如果保存失败会崩溃
4. **路径拼接不安全** - 可能导致路径遍历攻击

请修改以上问题。"""
    }

    # 为Developer的第二次迭代添加响应
    llm_client = create_llm_client("mock", responses=mock_responses)

    # 手动添加第二次迭代的响应
    llm_client.responses["Developer_iteration_2"] = """# 文件上传代码（第2版 - 已修改）

```python
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(file):
    try:
        # 1. 验证文件类型
        if not allowed_file(file.filename):
            return {"success": False, "message": "不支持的文件类型"}

        # 2. 验证文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return {"success": False, "message": "文件大小超过限制"}

        # 3. 安全的文件名处理
        filename = secure_filename(file.filename)

        # 4. 保存文件（带错误处理）
        filepath = os.path.join('/uploads', filename)
        file.save(filepath)

        return {"success": True, "filename": filename}

    except Exception as e:
        return {"success": False, "message": f"上传失败: {str(e)}"}
```

修改说明：
1. ✅ 添加了文件类型验证
2. ✅ 添加了文件大小验证
3. ✅ 添加了完整的错误处理
4. ✅ 使用secure_filename防止路径遍历攻击"""

    llm_client.responses["CodeReviewer_iteration_2"] = """# 代码审查结果（第2次）

✅ 审查通过

修改确认：
1. ✅ 已添加文件类型验证（ALLOWED_EXTENSIONS）
2. ✅ 已添加文件大小验证（MAX_FILE_SIZE）
3. ✅ 已添加完整的错误处理（try-except）
4. ✅ 已使用secure_filename防止路径遍历

代码质量良好，所有问题已解决，批准通过。"""

    # 2. 创建Agent
    print("2. 创建Agent...\n")
    requester = SimplifiedRequesterAgent(llm_client)
    developer = SimplifiedDeveloperAgent(llm_client)
    code_reviewer = SimplifiedCodeReviewerAgent(llm_client)

    # 3. 创建任务
    print("3. 创建任务...\n")
    task = Task(
        task_id="task-002",
        title="实现文件上传功能",
        description="需要实现一个安全的文件上传功能，支持图片和文档格式，限制文件大小。"
    )

    # 4. 创建Orchestrator
    print("4. 创建Orchestrator...\n")
    orchestrator = SimpleOrchestrator(
        agents=[requester, developer, code_reviewer],
        max_iterations=5
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

    # 7. 输出迭代统计
    print("\n" + "="*60)
    print("迭代统计")
    print("="*60)
    for agent_name, count in task.iteration_count.items():
        print(f"{agent_name}: {count}次")

    # 8. 输出对话历史
    if task.conversation:
        print("\n" + "="*60)
        print("对话历史")
        print("="*60)
        for i, msg in enumerate(task.conversation.messages, 1):
            print(f"\n{i}. [{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}")
            content_preview = str(msg.content)[:80]
            print(f"   内容: {content_preview}...")

    # 9. 输出产物版本
    print("\n" + "="*60)
    print("产物版本")
    print("="*60)
    for artifact in task.artifacts:
        print(f"\n类型: {artifact['type']}")
        print(f"Agent: {artifact['agent']}")
        print(f"版本: {artifact['version']}")
        print(f"时间: {artifact['timestamp']}")


if __name__ == "__main__":
    main()
