"""
综合测试场景 - 使用Mock LLM

测试内容：
1. 正常流程：需求→开发→审查→测试→部署
2. 代码审查失败：Developer修改后通过
3. 测试失败：Developer修复Bug后通过
4. 迭代超限：触发人工介入
5. 对话历史和产物版本管理

目标：
- 验证系统的完整性
- 验证各种边界情况
- 验证收敛机制
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


# ==================== Agent定义 ====================

class RequesterAgent(BaseAgent):
    """需求分析Agent"""
    def __init__(self, llm_client):
        super().__init__("Requester", "需求分析师", llm_client=llm_client)
        self.principles = ["需求必须清晰", "不能遗漏关键信息"]

    def _get_responsibilities(self) -> str:
        return "分析需求，输出结构化文档"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 分析需求...")
        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))
        return {'success': True, 'output': response}


class DeveloperAgent(BaseAgent):
    """开发Agent"""
    def __init__(self, llm_client):
        super().__init__("Developer", "开发工程师", llm_client=llm_client)
        self.principles = ["代码必须有错误处理", "代码必须有注释"]

    def _get_responsibilities(self) -> str:
        return "编写高质量代码"

    def process(self, task) -> Dict[str, Any]:
        feedback = self._check_feedback(task)
        if feedback:
            print(f"\n[{self.name}] 收到反馈，修改代码...")
        else:
            print(f"\n[{self.name}] 开发代码...")

        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))
        return {'success': True, 'output': response}


class CodeReviewerAgent(BaseAgent):
    """代码审查Agent"""
    def __init__(self, llm_client, strict_mode=False):
        super().__init__("CodeReviewer", "代码审查员", llm_client=llm_client)
        self.principles = ["代码规范不能妥协", "错误处理必须完整"]
        self.strict_mode = strict_mode  # 严格模式：第一次必定发现问题

    def _get_responsibilities(self) -> str:
        return "审查代码质量"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 审查代码...")
        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

        # 严格模式：第一次迭代必定发现问题
        if self.strict_mode and task.get_iteration_count("Developer") == 1:
            print(f"[{self.name}] ❌ 发现问题")
            self._send_message(task, "Developer", response, MessageType.REVISION_REQUEST)
            return {'success': False, 'action': 'revise', 'next_agent': 'Developer'}

        # 判断是否通过
        if "通过" in response:
            print(f"[{self.name}] ✅ 审查通过")
            self._send_message(task, "Developer", "审查通过", MessageType.APPROVAL)
            return {'success': True, 'output': response}
        else:
            print(f"[{self.name}] ❌ 需要修改")
            self._send_message(task, "Developer", response, MessageType.REVISION_REQUEST)
            return {'success': False, 'action': 'revise', 'next_agent': 'Developer'}


class TesterAgent(BaseAgent):
    """测试Agent"""
    def __init__(self, llm_client, find_bug_on_first=False):
        super().__init__("Tester", "测试工程师", llm_client=llm_client)
        self.principles = ["测试覆盖率必须充足", "Bug必须修复"]
        self.find_bug_on_first = find_bug_on_first

    def _get_responsibilities(self) -> str:
        return "编写测试用例，执行测试"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 执行测试...")
        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

        # 第一次测试发现Bug
        if self.find_bug_on_first and task.get_iteration_count("Developer") == 1:
            print(f"[{self.name}] ❌ 发现Bug")
            self._send_message(task, "Developer", "发现Bug：边界情况处理不当", MessageType.OBJECTION)
            return {'success': False, 'action': 'revise', 'next_agent': 'Developer'}

        print(f"[{self.name}] ✅ 测试通过")
        return {'success': True, 'output': response}


class DevOpsAgent(BaseAgent):
    """运维Agent"""
    def __init__(self, llm_client):
        super().__init__("DevOps", "运维工程师", llm_client=llm_client)
        self.principles = ["部署必须稳定", "监控必须完备"]

    def _get_responsibilities(self) -> str:
        return "准备部署环境，执行部署"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 执行部署...")
        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))
        print(f"[{self.name}] ✅ 部署完成")
        return {'success': True, 'output': response}


# ==================== 测试场景 ====================

def test_scenario_1_normal_flow():
    """场景1：正常流程，一次通过"""
    print("\n" + "="*60)
    print("场景1：正常流程（一次通过）")
    print("="*60)

    mock_responses = {
        "Requester": "# 需求文档\n\n实现用户登录功能",
        "Developer": "# 登录代码\n\n```python\ndef login(username, password):\n    return True\n```",
        "CodeReviewer": "✅ 代码审查通过",
        "Tester": "✅ 测试通过",
        "DevOps": "✅ 部署完成"
    }

    llm_client = create_llm_client("mock", responses=mock_responses)

    agents = [
        RequesterAgent(llm_client),
        DeveloperAgent(llm_client),
        CodeReviewerAgent(llm_client, strict_mode=False),
        TesterAgent(llm_client, find_bug_on_first=False),
        DevOpsAgent(llm_client)
    ]

    task = Task("task-001", "实现用户登录", "实现简单的用户登录功能")
    orchestrator = SimpleOrchestrator(agents, max_iterations=5)

    result = orchestrator.execute(task)

    print(f"\n结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"迭代统计: {dict(task.iteration_count)}")
    print(f"产物数量: {len(task.artifacts)}")

    return result['success']


def test_scenario_2_code_review_fail():
    """场景2：代码审查失败，Developer修改后通过"""
    print("\n" + "="*60)
    print("场景2：代码审查失败（需要修改）")
    print("="*60)

    mock_responses = {
        "Requester": "# 需求文档\n\n实现文件上传功能",
        "Developer": "# 文件上传代码（第1版）\n\n```python\ndef upload(file):\n    file.save()\n```",
        "CodeReviewer": "❌ 缺少文件类型验证和大小限制",
    }

    llm_client = create_llm_client("mock", responses=mock_responses)

    # 为第二次迭代添加响应
    llm_client.responses["Developer_iteration_2"] = "# 文件上传代码（第2版）\n\n```python\ndef upload(file):\n    if not allowed(file):\n        return False\n    file.save()\n```"
    llm_client.responses["CodeReviewer_iteration_2"] = "✅ 代码审查通过"

    agents = [
        RequesterAgent(llm_client),
        DeveloperAgent(llm_client),
        CodeReviewerAgent(llm_client, strict_mode=True),  # 严格模式
        TesterAgent(llm_client, find_bug_on_first=False),
        DevOpsAgent(llm_client)
    ]

    task = Task("task-002", "实现文件上传", "实现安全的文件上传功能")
    orchestrator = SimpleOrchestrator(agents, max_iterations=5)

    result = orchestrator.execute(task)

    print(f"\n结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"迭代统计: {dict(task.iteration_count)}")
    print(f"产物数量: {len(task.artifacts)}")
    print(f"对话数量: {len(task.conversation.messages) if task.conversation else 0}")

    return result['success']


def test_scenario_3_test_fail():
    """场景3：测试失败，Developer修复Bug后通过"""
    print("\n" + "="*60)
    print("场景3：测试失败（发现Bug）")
    print("="*60)

    mock_responses = {
        "Requester": "# 需求文档\n\n实现数据验证功能",
        "Developer": "# 验证代码\n\n```python\ndef validate(data):\n    return True\n```",
        "CodeReviewer": "✅ 代码审查通过",
        "Tester": "❌ 发现Bug：边界情况处理不当",
    }

    llm_client = create_llm_client("mock", responses=mock_responses)

    # 为修复后的迭代添加响应
    llm_client.responses["Developer_iteration_2"] = "# 验证代码（修复版）\n\n```python\ndef validate(data):\n    if data is None:\n        return False\n    return True\n```"
    llm_client.responses["CodeReviewer_iteration_2"] = "✅ 代码审查通过"
    llm_client.responses["Tester_iteration_2"] = "✅ 测试通过"

    agents = [
        RequesterAgent(llm_client),
        DeveloperAgent(llm_client),
        CodeReviewerAgent(llm_client, strict_mode=False),
        TesterAgent(llm_client, find_bug_on_first=True),  # 第一次发现Bug
        DevOpsAgent(llm_client)
    ]

    task = Task("task-003", "实现数据验证", "实现健壮的数据验证功能")
    orchestrator = SimpleOrchestrator(agents, max_iterations=5)

    result = orchestrator.execute(task)

    print(f"\n结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"迭代统计: {dict(task.iteration_count)}")
    print(f"产物数量: {len(task.artifacts)}")

    return result['success']


def test_scenario_4_iteration_limit():
    """场景4：迭代超限，触发人工介入"""
    print("\n" + "="*60)
    print("场景4：迭代超限（人工介入）")
    print("="*60)

    mock_responses = {
        "Requester": "# 需求文档\n\n实现复杂算法",
        "Developer": "# 算法代码\n\n```python\ndef algorithm():\n    pass\n```",
        "CodeReviewer": "❌ 算法实现有问题",  # 永远不通过
    }

    llm_client = create_llm_client("mock", responses=mock_responses)

    agents = [
        RequesterAgent(llm_client),
        DeveloperAgent(llm_client),
        CodeReviewerAgent(llm_client, strict_mode=True),  # 严格模式，永远不通过
    ]

    task = Task("task-004", "实现复杂算法", "实现一个复杂的算法")
    orchestrator = SimpleOrchestrator(agents, max_iterations=3)  # 降低限制

    result = orchestrator.execute(task)

    print(f"\n结果: {'✅ 成功' if result['success'] else '❌ 失败（预期）'}")
    print(f"迭代统计: {dict(task.iteration_count)}")
    print(f"是否升级人工: {'是' if 'escalation' in result else '否'}")

    return not result['success']  # 预期失败


def print_task_details(task):
    """打印任务详情"""
    print("\n" + "-"*60)
    print("任务详情")
    print("-"*60)

    print(f"\n任务ID: {task.task_id}")
    print(f"标题: {task.title}")
    print(f"状态: {task.status.value}")

    print(f"\n迭代统计:")
    for agent, count in task.iteration_count.items():
        print(f"  {agent}: {count}次")

    print(f"\n产物列表 ({len(task.artifacts)}个):")
    for i, artifact in enumerate(task.artifacts, 1):
        print(f"  {i}. [{artifact['agent']}] {artifact['type']} v{artifact['version']}")

    if task.conversation:
        print(f"\n对话历史 ({len(task.conversation.messages)}条):")
        for i, msg in enumerate(task.conversation.messages, 1):
            print(f"  {i}. [{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("综合测试：多种场景")
    print("="*60)

    results = []

    # 场景1：正常流程
    results.append(("场景1：正常流程", test_scenario_1_normal_flow()))

    # 场景2：代码审查失败
    results.append(("场景2：代码审查失败", test_scenario_2_code_review_fail()))

    # 场景3：测试失败
    results.append(("场景3：测试失败", test_scenario_3_test_fail()))

    # 场景4：迭代超限
    results.append(("场景4：迭代超限", test_scenario_4_iteration_limit()))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\n总计: {passed}/{total} 通过")


if __name__ == "__main__":
    main()
