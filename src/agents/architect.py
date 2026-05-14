"""
Architect Agent
架构师：设计技术架构和系统方案

职责：
1. 接收PRD文档
2. 设计技术架构（前端、后端、数据库、部署）
3. 选择技术栈
4. 设计数据模型和API接口
5. 考虑性能、安全、扩展性

改进点：
- 使用LLM生成专业的架构设计
- 结构化的架构文档
- 考虑技术可行性和最佳实践
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import get_config_loader, LLMFactory, LLMClient, LLMError


class ArchitectAgent(BaseAgent):
    """
    架构师Agent

    负责根据PRD设计技术架构，
    选择技术栈，设计系统结构。
    """

    def __init__(self, name: str = "Architect", config: Dict[str, Any] = None):
        super().__init__(name, "架构师", config)
        self.llm_client: Optional[LLMClient] = None
        self._initialize_llm()

    def _initialize_llm(self):
        """初始化LLM客户端"""
        try:
            loader = get_config_loader()
            llm_config = loader.get_agent_config(self.name)
            self.llm_client = LLMFactory.create(llm_config)
            print(f"[{self.name}] ✓ LLM客户端初始化成功")
        except Exception as e:
            print(f"[{self.name}] ⚠️  LLM客户端初始化失败: {str(e)}")
            self.llm_client = None

    def _build_system_prompt(self) -> str:
        """构建系统提示词 - 定义架构师角色"""
        return """你是资深系统架构师，负责设计技术架构。

输出JSON格式，包含：
- architecture_overview: 架构概述
- technology_stack: 技术栈选择
- system_components: 系统组件
- data_model: 数据模型
- api_design: API设计
- non_functional_design: 性能/安全/扩展性设计

注意：技术选型要合理，架构要清晰易实现。"""

    def _build_user_prompt(self, task: Task) -> str:
        """构建用户提示词"""
        prd = None
        for artifact in task.artifacts:
            if artifact.get('type') == 'prd':
                prd = artifact.get('content')
                break

        prompt = f"请为产品'{task.title}'设计技术架构。\n"
        if prd:
            prompt += f"功能需求：{len(prd.get('functional_requirements', []))}个\n"
        return prompt

    def _design_with_llm(self, task: Task) -> Dict[str, Any]:
        """使用LLM设计架构"""
        print(f"[{self.name}] 使用LLM设计架构...")
        response = self.llm_client.call(
            prompt=self._build_user_prompt(task),
            system_prompt=self._build_system_prompt(),
            temperature=0.5,
            max_tokens=4096
        )
        try:
            return json.loads(response.content)
        except:
            return self._design_basic(task)

    def _design_basic(self, task: Task) -> Dict[str, Any]:
        """简单模式"""
        return {
            "architecture_overview": {"architecture_style": "三层架构"},
            "technology_stack": {
                "frontend": {"framework": "React"},
                "backend": {"framework": "FastAPI"},
                "database": {"name": "PostgreSQL"}
            }
        }

    def process(self, task: Task) -> Dict[str, Any]:
        """处理任务"""
        print(f"\n{'='*80}\n[{self.name}] 开始设计架构\n{'='*80}")
        task.update_status(TaskStatus.IN_DESIGN, self.name)

        try:
            architecture = self._design_with_llm(task) if self.llm_client else self._design_basic(task)

            print(f"[{self.name}] ✓ 架构设计完成")
            task.add_artifact(artifact_type="architecture_design", content=architecture, agent=self.name)

            return {
                'success': True,
                'message': '架构设计已完成',
                'next_agent': 'Developer',
                'architecture': architecture
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'next_agent': None}
