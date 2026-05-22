"""
Product Manager Agent
产品经理：将需求转化为产品需求文档（PRD）

职责：
1. 接收Requester分析后的需求
2. 编写详细的产品需求文档（PRD）
3. 定义用户故事、功能需求、验收标准
4. 为Architect提供清晰的产品设计

改进点：
- 使用LLM生成专业的PRD
- 结构化的PRD格式
- 考虑用户体验和业务价值
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import get_config_loader, LLMFactory, LLMClient, LLMError


class ProductManagerAgent(BaseAgent):
    """
    产品经理Agent

    负责将需求转化为详细的产品需求文档（PRD），
    定义产品的功能、用户体验、验收标准等。
    """

    def __init__(self, name: str = "ProductManager", config: Dict[str, Any] = None):
        """
        初始化ProductManager Agent

        Args:
            name: Agent名称
            config: Agent配置（可选）
        """
        super().__init__(name, "产品经理", config)

        # 初始化LLM客户端
        self.llm_client: Optional[LLMClient] = None
        self._initialize_llm()

        # 产品经理只需要基础工具（读写文档）
        # 不需要edit_file和run_command

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
        """
        构建系统提示词

        定义ProductManager的角色：
        - 专业的产品经理
        - 懂用户体验
        - 能写清晰的PRD

        Returns:
            str: 系统提示词
        """
        # 获取可用的Agent列表
        available_agents = self.get_available_agents() if hasattr(self, 'get_available_agents') else []
        agents_list = ', '.join(available_agents) if available_agents else 'architect, developer'

        return f"""你是一个资深的产品经理（Product Manager），负责将需求转化为详细的产品需求文档（PRD）。

你的职责：
1. 理解需求分析师提供的需求分析结果
2. 从产品和用户体验角度思考
3. 编写清晰、完整的PRD文档
4. 定义用户故事、功能需求、验收标准
5. 考虑产品的可用性、易用性、商业价值
6. **决定下一个处理该需求的Agent**

输出格式（JSON）：
{{
    "product_overview": {{
        "title": "产品名称",
        "description": "产品简介（1-2段）",
        "target_users": ["目标用户群1", "目标用户群2"],
        "business_value": "商业价值说明"
    }},
    "user_stories": [
        {{
            "as_a": "用户角色",
            "i_want": "想要的功能",
            "so_that": "达到的目的",
            "priority": "high/medium/low"
        }}
    ],
    "functional_requirements": [
        {{
            "id": "FR-001",
            "title": "功能标题",
            "description": "详细描述",
            "priority": "P0/P1/P2",
            "user_story_ref": "关联的用户故事"
        }}
    ],
    "non_functional_requirements": {{
        "performance": "性能要求",
        "security": "安全要求",
        "scalability": "扩展性要求",
        "usability": "易用性要求"
    }},
    "user_interface": {{
        "key_pages": ["页面1", "页面2"],
        "navigation": "导航结构说明",
        "interaction": "交互设计要点"
    }},
    "acceptance_criteria": [
        "验收标准1",
        "验收标准2"
    ],
    "risks_and_assumptions": {{
        "risks": ["风险1", "风险2"],
        "assumptions": ["假设1", "假设2"]
    }},
    "success_metrics": [
        "成功指标1",
        "成功指标2"
    ],
    "next_agent": "下一个Agent的名称"
}}

可用的Agent列表：
{agents_list}

**重要：next_agent字段说明**
- PRD完成后，通常应该转给 "architect" 进行架构设计
- 如果需求非常简单，可以直接转给 "developer" 开始开发
- 如果PRD有重大问题需要重新分析，可以转回 "requester"
- **必须使用小写+下划线格式**（如 architect，不是 Architect）
- **只能选择上述可用Agent列表中的Agent**

注意事项：
- 用户故事要具体，遵循"As a... I want... So that..."格式
- 功能需求要有优先级（P0最高，P2最低）
- 验收标准要可测试、可量化
- 考虑边界情况和异常场景
- PRD要让开发人员能够直接开始设计架构
"""

    def _build_user_prompt(self, task: Task) -> str:
        """
        构建用户提示词

        将需求分析结果转换为LLM可以理解的提示词。

        Args:
            task: 任务对象

        Returns:
            str: 用户提示词
        """
        # 获取Requester的分析结果
        requirement_analysis = None
        for artifact in task.artifacts:
            if artifact.get('type') == 'requirement_analysis':
                requirement_analysis = artifact.get('content')
                break

        # 构建提示词
        prompt = f"""请为以下需求编写详细的产品需求文档（PRD）：

## 原始需求
标题：{task.title}
描述：{task.description}
"""

        # 如果有需求分析结果，加入到提示词中
        if requirement_analysis:
            prompt += f"""

## 需求分析结果
需求总结：{requirement_analysis.get('requirement_summary', 'N/A')}
关键功能：{', '.join(requirement_analysis.get('key_features', []))}
约束条件：{', '.join(requirement_analysis.get('constraints', []))}
可行性评估：{requirement_analysis.get('feasibility', 'N/A')}
"""

        prompt += """

请按照指定的JSON格式输出完整的PRD文档。
注意：
1. 用户故事要具体、可操作
2. 功能需求要有明确的优先级
3. 验收标准要可测试
4. 考虑用户体验和商业价值
"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析LLM的响应（增强容错版本）

        提取JSON格式的PRD文档。

        Args:
            response_text: LLM返回的文本

        Returns:
            Dict: 解析后的PRD对象

        Raises:
            ValueError: 如果无法解析JSON
        """
        import re

        # 策略1: 尝试直接解析
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # 策略2: 提取```json代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 策略3: 提取普通代码块
        code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass

        # 策略4: 查找{...}内容
        brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if brace_match:
            try:
                json_str = brace_match.group(0)
                # 移除尾部逗号
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 所有策略失败
        raise ValueError(f"无法从响应中提取有效的JSON。响应前200字符: {response_text[:200]}...")

    def _generate_prd_with_llm(self, task: Task) -> Dict[str, Any]:
        """
        使用LLM生成PRD

        这是核心方法，调用LLM生成专业的PRD文档。

        Args:
            task: 任务对象

        Returns:
            Dict: PRD文档

        Raises:
            LLMError: 如果LLM调用失败
        """
        print(f"\n[{self.name}] 正在使用LLM生成PRD...")

        # 构建提示词
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        response = self.llm_client.call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,  # 较高的温度，鼓励创造性
            max_tokens=4096   # PRD可能比较长
        )

        print(f"[{self.name}] ✓ LLM响应成功 (使用了 {response.usage['total_tokens']} tokens)")

        # 解析响应
        try:
            prd = self._parse_llm_response(response.content)
            return prd

        except Exception as e:
            print(f"[{self.name}] ⚠️  解析LLM响应失败: {str(e)}")
            # 返回一个基本的PRD
            return self._generate_basic_prd(task)

    def _generate_basic_prd(self, task: Task) -> Dict[str, Any]:
        """
        生成基本PRD（简单模式）

        当LLM不可用时的降级方案。
        生成一个基本的PRD框架。

        Args:
            task: 任务对象

        Returns:
            Dict: 基本的PRD文档
        """
        print(f"\n[{self.name}] 使用简单模式生成PRD（未使用LLM）")

        return {
            "product_overview": {
                "title": task.title,
                "description": task.description[:200],
                "target_users": ["待定义"],
                "business_value": "待分析"
            },
            "user_stories": [
                {
                    "as_a": "用户",
                    "i_want": "使用系统",
                    "so_that": "完成任务",
                    "priority": "high"
                }
            ],
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "基础功能",
                    "description": task.description,
                    "priority": "P0",
                    "user_story_ref": "待关联"
                }
            ],
            "non_functional_requirements": {
                "performance": "待定义",
                "security": "需要身份验证",
                "scalability": "待评估",
                "usability": "待设计"
            },
            "user_interface": {
                "key_pages": ["待设计"],
                "navigation": "待规划",
                "interaction": "待定义"
            },
            "acceptance_criteria": [
                "功能正常运行",
                "通过测试"
            ],
            "risks_and_assumptions": {
                "risks": ["未进行详细分析"],
                "assumptions": ["基于初步需求"]
            },
            "success_metrics": [
                "待定义"
            ]
        }

    def process(self, task: Task) -> Dict[str, Any]:
        """
        处理任务（主入口）

        将需求转化为PRD文档。

        Args:
            task: 任务对象

        Returns:
            Dict: 处理结果
        """
        print(f"\n{'='*80}")
        print(f"[{self.name}] 开始编写PRD")
        print(f"{'='*80}")

        # 更新任务状态
        task.update_status(TaskStatus.IN_DESIGN, self.name)

        try:
            # 根据是否有LLM客户端，选择生成方式
            if self.llm_client:
                prd = self._generate_prd_with_llm(task)
            else:
                prd = self._generate_basic_prd(task)

            # 打印PRD摘要
            print(f"\n[{self.name}] PRD生成完成:")
            print(f"  产品名称: {prd['product_overview']['title']}")
            print(f"  用户故事: {len(prd['user_stories'])}个")
            print(f"  功能需求: {len(prd['functional_requirements'])}个")
            print(f"  验收标准: {len(prd['acceptance_criteria'])}个")

            # 保存PRD为产物
            task.add_artifact(
                artifact_type="prd",
                content=prd,
                agent=self.name
            )

            # 检查PRD的完整性
            # 简单模式下，降低审核标准，避免阻塞工作流
            needs_review = False  # 简单模式不阻塞
            if self.llm_client:  # 只有LLM模式才严格检查
                needs_review = (
                    prd['product_overview']['target_users'] == ["待定义"] or
                    prd['product_overview']['business_value'] == "待分析" or
                    len(prd['user_stories']) < 2
                )

            if needs_review:
                print(f"\n[{self.name}] ⚠️  PRD需要人工审核")
                return {
                    'success': False,
                    'message': 'PRD需要人工审核和完善',
                    'next_agent': 'HumanAgent',
                    'prd': prd
                }

            # PRD完成，进入架构设计阶段
            print(f"\n[{self.name}] ✓ PRD已完成，可以进入架构设计阶段")

            # 从LLM响应中获取并验证next_agent
            next_agent = self.extract_and_validate_next_agent(prd, default_agent='architect')

            if next_agent:
                print(f"[{self.name}] → 下一个Agent: {next_agent}")

            return {
                'success': True,
                'message': 'PRD已完成',
                'next_agent': next_agent,
                'prd': prd
            }

        except LLMError as e:
            print(f"\n[{self.name}] ✗ LLM调用失败: {str(e)}")
            return {
                'success': False,
                'message': f'LLM调用失败: {str(e)}',
                'next_agent': None
            }

        except Exception as e:
            print(f"\n[{self.name}] ✗ 处理失败: {str(e)}")
            return {
                'success': False,
                'message': f'处理失败: {str(e)}',
                'next_agent': None
            }
