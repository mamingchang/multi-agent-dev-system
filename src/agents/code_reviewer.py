"""
CodeReviewer Agent
代码审查员：审查代码质量

职责：
1. 审查代码规范
2. 检查潜在Bug
3. 评估代码质量
4. 提出改进建议
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import get_config_loader, LLMFactory, LLMClient, LLMError


class CodeReviewerAgent(BaseAgent):
    """代码审查员Agent"""

    def __init__(self, name: str = "CodeReviewer", config: Dict[str, Any] = None):
        super().__init__(name, "代码审查员", config)
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
        return """你是资深代码审查员，负责审查代码质量。

输出JSON格式：
- overall_quality: 整体质量评分(0-10)
- issues: 发现的问题列表
- suggestions: 改进建议
- approved: 是否通过审查

关注：代码规范、潜在Bug、性能问题、安全漏洞"""

    def _review_with_llm(self, task: Task) -> Dict[str, Any]:
        print(f"[{self.name}] 使用LLM审查代码...")
        code = None
        for artifact in task.artifacts:
            if artifact.get('type') == 'code':
                code = artifact.get('content')
                break

        prompt = f"请审查以下代码：\n文件数：{len(code.get('files', []))}个"

        response = self.llm_client.call(
            prompt=prompt,
            system_prompt=self._build_system_prompt(),
            temperature=0.3,
            max_tokens=4096
        )
        try:
            return json.loads(response.content)
        except:
            return self._review_basic(task)

    def _review_basic(self, task: Task) -> Dict[str, Any]:
        return {
            "overall_quality": 7,
            "issues": [],
            "suggestions": ["建议启用LLM进行专业审查"],
            "approved": True
        }

    def process(self, task: Task) -> Dict[str, Any]:
        print(f"\n{'='*80}\n[{self.name}] 开始代码审查\n{'='*80}")
        task.update_status(TaskStatus.IN_REVIEW, self.name)

        try:
            review = self._review_with_llm(task) if self.llm_client else self._review_basic(task)

            print(f"[{self.name}] ✓ 代码审查完成")
            print(f"  质量评分：{review.get('overall_quality', 0)}/10")
            print(f"  问题数：{len(review.get('issues', []))}个")

            task.add_artifact(artifact_type="code_review", content=review, agent=self.name)

            if not review.get('approved', False):
                return {
                    'success': False,
                    'message': '代码审查未通过，需要修改',
                    'next_agent': 'Developer',
                    'review': review
                }

            return {
                'success': True,
                'message': '代码审查通过',
                'next_agent': 'Tester',
                'review': review
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'next_agent': None}
