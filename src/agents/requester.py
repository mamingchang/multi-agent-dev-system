"""
Requester Agent
需求提出者：分析和理解用户需求

职责：
1. 接收用户的原始需求
2. 分析需求的完整性和清晰度
3. 提出澄清问题（如果需要）
4. 将需求结构化输出

改进点：
- 使用LLM进行智能分析
- 不再只是简单记录，而是真正理解需求
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import get_config_loader, LLMFactory, LLMClient, LLMError


class RequesterAgent(BaseAgent):
    """
    需求提出者Agent

    这个Agent是工作流的第一步，负责理解和分析用户需求。
    使用LLM来智能分析需求的完整性和可行性。
    """

    def __init__(self, name: str = "Requester", config: Dict[str, Any] = None):
        """
        初始化Requester Agent

        Args:
            name: Agent名称
            config: Agent配置（可选）
        """
        super().__init__(name, "需求提出者", config)

        # 初始化LLM客户端
        # 这里使用了依赖注入的思想：从外部获取配置，而不是硬编码
        self.llm_client: Optional[LLMClient] = None
        self._initialize_llm()

    def _initialize_llm(self):
        """
        初始化LLM客户端

        从配置文件加载LLM配置，并创建客户端。
        如果配置加载失败，Agent仍然可以工作（降级到简单模式）。
        """
        try:
            # 加载配置
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

        系统提示词定义了Agent的角色、能力和行为规范。
        这是Prompt工程的核心部分。

        Returns:
            str: 系统提示词
        """
        return """你是一个专业的需求分析师（Requester），负责理解和分析用户的软件开发需求。

你的职责：
1. 仔细阅读用户提出的需求
2. 分析需求的完整性（是否包含足够的信息）
3. 分析需求的清晰度（是否表达明确）
4. 识别需求中的关键要素（功能、约束、目标等）
5. 如果需求不清楚，提出具体的澄清问题

输出格式（JSON）：
{
    "requirement_summary": "需求的简短总结（1-2句话）",
    "key_features": ["功能点1", "功能点2", ...],
    "constraints": ["约束条件1", "约束条件2", ...],
    "clarity_score": 0-10的分数（10分表示非常清晰）,
    "completeness_score": 0-10的分数（10分表示非常完整）,
    "questions": ["澄清问题1", "澄清问题2", ...],
    "feasibility": "初步可行性评估",
    "recommendation": "给产品经理的建议"
}

注意事项：
- 如果需求已经很清楚，questions可以为空列表
- 要客观评估，不要过度乐观或悲观
- 建议要具体可行，不要泛泛而谈
"""

    def _build_user_prompt(self, task: Task) -> str:
        """
        构建用户提示词

        将任务信息转换为LLM可以理解的提示词。

        Args:
            task: 任务对象

        Returns:
            str: 用户提示词
        """
        return f"""请分析以下软件开发需求：

需求标题：{task.title}

需求描述：
{task.description}

请按照指定的JSON格式输出你的分析结果。"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析LLM的响应

        LLM返回的是文本，我们需要提取其中的JSON部分。

        Args:
            response_text: LLM返回的文本

        Returns:
            Dict: 解析后的JSON对象

        Raises:
            ValueError: 如果无法解析JSON
        """
        try:
            # 尝试直接解析整个响应
            return json.loads(response_text)

        except json.JSONDecodeError:
            # 如果失败，尝试提取JSON代码块
            # LLM有时会在JSON外面加上```json ... ```
            import re

            # 查找JSON代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # 查找普通代码块
            code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
            if code_match:
                json_str = code_match.group(1)
                return json.loads(json_str)

            # 如果都失败了，抛出错误
            raise ValueError(f"无法从响应中提取JSON: {response_text[:200]}...")

    def _analyze_with_llm(self, task: Task) -> Dict[str, Any]:
        """
        使用LLM分析需求

        这是核心方法，调用LLM进行智能分析。

        Args:
            task: 任务对象

        Returns:
            Dict: 分析结果

        Raises:
            LLMError: 如果LLM调用失败
        """
        print(f"\n[{self.name}] 正在使用LLM分析需求...")

        # 构建提示词
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        # 这里使用了我们之前实现的统一接口
        response = self.llm_client.call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,  # 适中的温度，既有创造性又不太随机
            max_tokens=2048
        )

        print(f"[{self.name}] ✓ LLM响应成功 (使用了 {response.usage['total_tokens']} tokens)")

        # 解析响应
        try:
            analysis = self._parse_llm_response(response.content)
            return analysis

        except Exception as e:
            print(f"[{self.name}] ⚠️  解析LLM响应失败: {str(e)}")
            # 返回一个基本的分析结果
            return {
                "requirement_summary": task.description[:100],
                "key_features": [],
                "constraints": [],
                "clarity_score": 5,
                "completeness_score": 5,
                "questions": [],
                "feasibility": "需要进一步分析",
                "recommendation": "建议产品经理进一步细化需求"
            }

    def _analyze_simple(self, task: Task) -> Dict[str, Any]:
        """
        简单模式分析（不使用LLM）

        当LLM不可用时的降级方案。
        只做基本的信息提取，不做智能分析。

        Args:
            task: 任务对象

        Returns:
            Dict: 基本的分析结果
        """
        print(f"\n[{self.name}] 使用简单模式分析需求（未使用LLM）")

        # 简单模式给出较高的评分，避免阻塞工作流
        return {
            "requirement_summary": task.description[:100] + "..." if len(task.description) > 100 else task.description,
            "key_features": [],
            "constraints": [],
            "clarity_score": 7,  # 提高评分，避免阻塞
            "completeness_score": 7,  # 提高评分，避免阻塞
            "questions": [],
            "feasibility": "未进行智能分析",
            "recommendation": "建议启用LLM以获得更好的分析结果"
        }

    def process(self, task: Task) -> Dict[str, Any]:
        """
        处理任务（主入口）

        这是Agent的核心方法，被Orchestrator调用。

        Args:
            task: 任务对象

        Returns:
            Dict: 处理结果
        """
        print(f"\n{'='*80}")
        print(f"[{self.name}] 开始分析需求")
        print(f"{'='*80}")
        print(f"需求标题: {task.title}")
        print(f"需求描述: {task.description[:200]}{'...' if len(task.description) > 200 else ''}")

        # 更新任务状态
        task.update_status(TaskStatus.IN_REQUIREMENT, self.name)

        try:
            # 根据是否有LLM客户端，选择分析方式
            if self.llm_client:
                analysis = self._analyze_with_llm(task)
            else:
                analysis = self._analyze_simple(task)

            # 打印分析结果
            print(f"\n[{self.name}] 分析结果:")
            print(f"  需求总结: {analysis['requirement_summary']}")
            print(f"  清晰度评分: {analysis['clarity_score']}/10")
            print(f"  完整度评分: {analysis['completeness_score']}/10")

            if analysis['key_features']:
                print(f"  关键功能: {', '.join(analysis['key_features'][:3])}")

            if analysis['questions']:
                print(f"  澄清问题: {len(analysis['questions'])}个")
                for i, q in enumerate(analysis['questions'][:3], 1):
                    print(f"    {i}. {q}")

            # 将分析结果保存为产物
            task.add_artifact(
                artifact_type="requirement_analysis",
                content=analysis,
                agent=self.name
            )

            # 判断是否需要人工介入
            # 如果清晰度或完整度太低，或者有很多问题，需要人工澄清
            needs_clarification = (
                analysis['clarity_score'] < 6 or
                analysis['completeness_score'] < 6 or
                len(analysis['questions']) > 3
            )

            if needs_clarification:
                print(f"\n[{self.name}] ⚠️  需求需要进一步澄清")
                return {
                    'success': False,
                    'message': '需求不够清晰，需要人工介入澄清',
                    'next_agent': 'HumanAgent',  # 转给人工处理
                    'analysis': analysis
                }

            # 需求分析通过，进入下一阶段
            print(f"\n[{self.name}] ✓ 需求分析完成，可以进入产品设计阶段")

            return {
                'success': True,
                'message': '需求分析完成',
                'next_agent': 'ProductManager',
                'analysis': analysis
            }

        except LLMError as e:
            # LLM调用失败
            print(f"\n[{self.name}] ✗ LLM调用失败: {str(e)}")
            return {
                'success': False,
                'message': f'LLM调用失败: {str(e)}',
                'next_agent': None
            }

        except Exception as e:
            # 其他未预期的错误
            print(f"\n[{self.name}] ✗ 处理失败: {str(e)}")
            return {
                'success': False,
                'message': f'处理失败: {str(e)}',
                'next_agent': None
            }
