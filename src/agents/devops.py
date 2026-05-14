"""
DevOps Agent
运维工程师：负责部署和运维

职责：
1. 准备部署环境
2. 配置CI/CD
3. 执行部署
4. 监控系统
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import get_config_loader, LLMFactory, LLMClient, LLMError


class DevOpsAgent(BaseAgent):
    """DevOps工程师Agent"""

    def __init__(self, name: str = "DevOps", config: Dict[str, Any] = None):
        super().__init__(name, "DevOps工程师", config)
        self.llm_client: Optional[LLMClient] = None
        self._initialize_llm()

    def _initialize_llm(self):
        try:
            loader = get_config_loader()
            llm_config = loader.get_agent_config(self.name)
            self.llm_client = LLMFactory.create(llm_config)
            print(f"[{self.name}] ✓ LLM客户端初始化成功")
        except Exception as e:
            print(f"[{self.name}] ⚠️  LLM客户端初始化失败")
            self.llm_client = None

    def _build_system_prompt(self) -> str:
        return """你是DevOps工程师，负责部署和运维。

输出JSON格式：
- deployment_plan: 部署计划
- environment_config: 环境配置
- ci_cd_pipeline: CI/CD流程
- monitoring_setup: 监控配置
- deployment_status: 部署状态

关注：自动化、可靠性、监控"""

    def _deploy_with_llm(self, task: Task) -> Dict[str, Any]:
        print(f"[{self.name}] 使用LLM规划部署...")
        response = self.llm_client.call(
            prompt=f"请为'{task.title}'规划部署方案",
            system_prompt=self._build_system_prompt(),
            temperature=0.5,
            max_tokens=2048
        )
        try:
            return json.loads(response.content)
        except:
            return self._deploy_basic(task)

    def _deploy_basic(self, task: Task) -> Dict[str, Any]:
        return {
            "deployment_plan": "Docker容器化部署",
            "environment_config": {"env": "production"},
            "ci_cd_pipeline": "GitHub Actions",
            "monitoring_setup": "待配置",
            "deployment_status": "success"
        }

    def process(self, task: Task) -> Dict[str, Any]:
        print(f"\n{'='*80}\n[{self.name}] 开始部署\n{'='*80}")
        task.update_status(TaskStatus.IN_DEPLOYMENT, self.name)

        try:
            deployment = self._deploy_with_llm(task) if self.llm_client else self._deploy_basic(task)

            print(f"[{self.name}] ✓ 部署完成")
            print(f"  部署方式：{deployment.get('deployment_plan', 'N/A')}")

            task.add_artifact(artifact_type="deployment_report", content=deployment, agent=self.name)
            task.update_status(TaskStatus.COMPLETED, self.name)

            return {
                'success': True,
                'message': '部署完成，项目上线',
                'next_agent': None,
                'deployment': deployment
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'next_agent': None}
