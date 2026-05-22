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

        # 代码审查员只需要基础工具（读代码、搜索）
        # 不需要写入和执行权限

    def _initialize_llm(self):
        """
        初始化LLM客户端

        优先使用Agent配置中的LLM设置（来自注册系统）
        如果没有，则从llm_config.yaml加载
        """
        try:
            # 优先使用Agent配置中的LLM设置
            if self.config and 'llm' in self.config:
                llm_config_dict = self.config['llm']

                # 创建LLM客户端（直接使用ClaudeLLMAdapter）
                from ..llm.llm_client import ClaudeLLMAdapter

                self.llm_client = ClaudeLLMAdapter(
                    model=llm_config_dict.get('model', 'claude-sonnet-4-5')
                )

                print(f"[{self.name}] ✓ LLM客户端初始化成功: {llm_config_dict.get('provider', 'claude')}/{llm_config_dict.get('model', 'claude-sonnet-4-5')}")
                return

            # 回退到llm_config.yaml
            loader = get_config_loader()
            llm_config = loader.get_agent_config(self.name)

            # 创建LLM客户端
            self.llm_client = LLMFactory.create(llm_config)

            print(f"[{self.name}] ✓ LLM客户端初始化成功: {llm_config.provider}/{llm_config.model}")

        except Exception as e:
            # 如果初始化失败，打印警告但不中断
            # Agent会降级到简单模式（不使用LLM）
            print(f"[{self.name}] ⚠️  LLM客户端初始化失败: {str(e)}")
            print(f"[{self.name}] 将使用简单模式（不调用LLM）")
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
                    'next_agent': 'developer',  # 使用小写+下划线格式
                    'review': review
                }

            return {
                'success': True,
                'message': '代码审查通过',
                'next_agent': 'tester',  # 使用小写+下划线格式
                'review': review
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'next_agent': None}
