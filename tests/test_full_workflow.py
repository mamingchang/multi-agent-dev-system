"""
测试完整的Agent工作流

场景：
1. Requester分析需求
2. Developer开发
3. CodeReviewer审查（可能要求修改）
4. Tester测试（可能发现Bug）
5. DevOps部署

验证完整的7个Agent协作流程
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


# 复用之前的Agent
class SimplifiedRequesterAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__("Requester", "需求分析师", llm_client=llm_client)

    def _get_responsibilities(self) -> str:
        return "分析用户需求"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 分析需求...")
        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))
        return {'success': True, 'output': response}


class SimplifiedDeveloperAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__("Developer", "开发工程师", llm_client=llm_client)

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


class SimplifiedCodeReviewerAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__("CodeReviewer", "代码审查员", llm_client=llm_client)

    def _get_responsibilities(self) -> str:
        return "审查代码质量"

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 审查代码...")
        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

        # 简单判断：如果响应包含"通过"，则通过
        if "通过" in response:
            print(f"[{self.name}] ✅ 审查通过")
            self._send_message(task, "Developer", "审查通过", MessageType.APPROVAL)
            return {'success': True, 'output': response}
        else:
            print(f"[{self.name}] ❌ 需要修改")
            self._send_message(task, "Developer", response, MessageType.REVISION_REQUEST)
            return {'success': False, 'action': 'revise', 'next_agent': 'Developer'}


# 新增：Tester Agent
class SimplifiedTesterAgent(BaseAgent):
    """简化的Tester Agent"""

    def __init__(self, llm_client):
        super().__init__("Tester", "测试工程师", llm_client=llm_client)
        self.principles = [
            "测试覆盖率必须充足",
            "Bug必须修复",
            "边界情况必须测试"
        ]

    def _get_responsibilities(self) -> str:
        return """1. 编写测试用例
2. 执行功能测试
3. 执行边界测试
4. 报告发现的Bug"""

    def _get_task_instruction(self, task) -> str:
        return """请对代码进行测试：
1. 编写测试用例
2. 测试正常情况
3. 测试边界情况
4. 测试异常情况

输出测试报告，包括：
- 测试用例列表
- 测试结果
- 发现的问题（如果有）"""

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 开始测试...")

        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

        print(f"[{self.name}] 测试完成")

        # 第一次测试发现Bug，第二次通过
        developer_iteration = task.get_iteration_count("Developer")

        if developer_iteration == 1:
            print(f"[{self.name}] ❌ 发现Bug，要求Developer修复")

            self._send_message(
                task,
                "Developer",
                "发现Bug：缺少邮箱格式验证",
                MessageType.OBJECTION
            )

            return {
                'success': False,
                'message': '发现Bug，需要修复',
                'action': 'revise',
                'next_agent': 'Developer'
            }
        else:
            print(f"[{self.name}] ✅ 测试通过")

            return {
                'success': True,
                'output': response,
                'message': '测试通过'
            }


# 新增：DevOps Agent
class SimplifiedDevOpsAgent(BaseAgent):
    """简化的DevOps Agent"""

    def __init__(self, llm_client):
        super().__init__("DevOps", "运维工程师", llm_client=llm_client)
        self.principles = [
            "部署必须稳定",
            "监控必须完备",
            "回滚方案必须准备"
        ]

    def _get_responsibilities(self) -> str:
        return """1. 准备部署环境
2. 执行部署
3. 配置监控
4. 验证部署结果"""

    def _get_task_instruction(self, task) -> str:
        return """请准备部署方案：
1. 部署步骤
2. 环境配置
3. 监控配置
4. 回滚方案

输出部署文档。"""

    def process(self, task) -> Dict[str, Any]:
        print(f"\n[{self.name}] 准备部署...")

        response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

        print(f"[{self.name}] ✅ 部署完成")

        return {
            'success': True,
            'output': response,
            'message': '部署完成'
        }


def main():
    """主函数"""
    print("\n" + "="*60)
    print("测试：完整的Agent工作流（5个Agent）")
    print("="*60 + "\n")

    # 1. 创建Mock LLM
    print("1. 创建Mock LLM...\n")
    mock_responses = {
        "Requester": """# 需求分析

## 功能
- 用户注册功能
- 邮箱验证

## 技术要求
- Python + Flask
- 发送验证邮件""",

        "Developer": """# 注册功能代码

```python
from flask import Flask, request
import smtplib

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    email = request.json['email']
    password = request.json['password']

    # 保存用户
    save_user(email, password)

    # 发送验证邮件
    send_verification_email(email)

    return {"success": True}
```""",

        "CodeReviewer": """# 审查结果

✅ 代码审查通过

代码质量良好，逻辑清晰。""",

        "Tester": """# 测试报告

## 测试用例
1. 正常注册 - ✅ 通过
2. 邮箱格式验证 - ✅ 通过
3. 密码强度验证 - ✅ 通过
4. 重复注册 - ✅ 通过

## 测试结果
所有测试用例通过，未发现Bug。""",

        "DevOps": """# 部署方案

## 部署步骤
1. 构建Docker镜像
2. 推送到镜像仓库
3. 更新Kubernetes配置
4. 滚动更新

## 监控配置
- 应用日志监控
- 性能指标监控
- 错误告警

## 回滚方案
如果部署失败，执行：
kubectl rollout undo deployment/app

部署完成！"""
    }

    llm_client = create_llm_client("mock", responses=mock_responses)

    # 2. 创建5个Agent
    print("2. 创建5个Agent...\n")
    requester = SimplifiedRequesterAgent(llm_client)
    developer = SimplifiedDeveloperAgent(llm_client)
    code_reviewer = SimplifiedCodeReviewerAgent(llm_client)
    tester = SimplifiedTesterAgent(llm_client)
    devops = SimplifiedDevOpsAgent(llm_client)

    # 3. 创建任务
    print("3. 创建任务...\n")
    task = Task(
        task_id="task-003",
        title="实现用户注册功能",
        description="实现用户注册功能，包括邮箱验证。"
    )

    # 4. 创建Orchestrator
    print("4. 创建Orchestrator（5个Agent）...\n")
    orchestrator = SimpleOrchestrator(
        agents=[requester, developer, code_reviewer, tester, devops],
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

    # 7. 输出Agent执行统计
    print("\n" + "="*60)
    print("Agent执行统计")
    print("="*60)
    for agent_name, count in task.iteration_count.items():
        print(f"{agent_name}: {count}次")

    # 8. 输出产物
    print("\n" + "="*60)
    print("产物列表")
    print("="*60)
    for artifact in task.artifacts:
        print(f"\n[{artifact['agent']}] {artifact['type']} (v{artifact['version']})")


if __name__ == "__main__":
    main()
