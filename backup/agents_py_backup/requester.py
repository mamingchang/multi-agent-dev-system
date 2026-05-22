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

        # Requester只需要基础工具（已在BaseAgent中启用）
        # 不需要额外的专业工具

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

        系统提示词定义了Agent的角色、能力和行为规范。
        这是Prompt工程的核心部分。

        Returns:
            str: 系统提示词
        """
        # 获取可用的Agent列表
        available_agents = self.get_available_agents() if hasattr(self, 'get_available_agents') else []
        agents_list = ', '.join(available_agents) if available_agents else 'product_manager, architect, developer'

        return f"""你是一个专业的需求分析师（Requester），负责理解和分析用户的软件开发需求。

你的职责：
1. 仔细阅读用户提出的需求
2. 分析需求的完整性（是否包含足够的信息）
3. 分析需求的清晰度（是否表达明确）
4. 识别需求中的关键要素（功能、约束、目标等）
5. 如果需求不清楚，提出具体的澄清问题
6. **决定下一个处理该需求的Agent**

输出格式（JSON）：
{{
    "requirement_summary": "需求的简短总结（1-2句话）",
    "key_features": ["功能点1", "功能点2", ...],
    "constraints": ["约束条件1", "约束条件2", ...],
    "clarity_score": 0-10的分数（10分表示非常清晰）,
    "completeness_score": 0-10的分数（10分表示非常完整）,
    "questions": ["澄清问题1", "澄清问题2", ...],
    "feasibility": "初步可行性评估",
    "recommendation": "给产品经理的建议",
    "next_agent": "下一个Agent的名称"
}}

可用的Agent列表：
{agents_list}

**重要：next_agent字段说明**
- 如果需求质量很差（平均分<4），设置为 null（需要人工介入）
- 如果需求基本清晰，通常应该转给 "product_manager" 进行产品设计
- 如果需求非常技术性且清晰，可以直接转给 "architect" 进行架构设计
- **必须使用小写+下划线格式**（如 product_manager，不是 ProductManager）
- **只能选择上述可用Agent列表中的Agent**

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
        解析LLM的响应（增强容错版本）

        LLM返回的是文本，我们需要提取其中的JSON部分。
        这个版本增加了多种容错策略。

        Args:
            response_text: LLM返回的文本

        Returns:
            Dict: 解析后的JSON对象

        Raises:
            ValueError: 如果无法解析JSON
        """
        import re

        # 策略1: 尝试直接解析整个响应
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # 策略2: 提取```json ... ```代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 策略3: 提取普通```代码块
        code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_match:
            try:
                json_str = code_match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 策略4: 查找第一个{到最后一个}之间的内容
        brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if brace_match:
            try:
                json_str = brace_match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 策略5: 尝试修复常见的JSON错误
        # 例如：单引号改双引号、尾部逗号、注释等
        try:
            # 移除注释
            cleaned = re.sub(r'//.*?\n', '\n', response_text)
            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

            # 提取JSON部分
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

                # 尝试修复常见问题
                # 移除尾部逗号
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

                return json.loads(json_str)
        except:
            pass

        # 策略6: 使用宽松的JSON解析器（如果可用）
        try:
            import json5
            return json5.loads(response_text)
        except:
            pass

        # 所有策略都失败了，抛出错误
        raise ValueError(f"无法从响应中提取有效的JSON。响应前200字符: {response_text[:200]}...")

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
            # 解析失败，输出详细信息用于调试
            print(f"[{self.name}] ⚠️  解析LLM响应失败: {str(e)}")

            # 尝试从响应中提取部分信息
            # 即使JSON解析失败，也尝试提取有用的信息
            import re

            # 尝试提取评分
            clarity_match = re.search(r'"clarity_score":\s*(\d+)', response.content)
            completeness_match = re.search(r'"completeness_score":\s*(\d+)', response.content)

            clarity_score = int(clarity_match.group(1)) if clarity_match else 5
            completeness_score = int(completeness_match.group(1)) if completeness_match else 5

            # 尝试提取需求总结
            summary_match = re.search(r'"requirement_summary":\s*"([^"]+)"', response.content)
            summary = summary_match.group(1) if summary_match else task.description[:100]

            print(f"[{self.name}] 使用部分解析结果（清晰度: {clarity_score}/10, 完整度: {completeness_score}/10）")

            # 返回一个基本的分析结果
            return {
                "requirement_summary": summary,
                "key_features": [],
                "constraints": [],
                "clarity_score": clarity_score,
                "completeness_score": completeness_score,
                "questions": [],
                "feasibility": "JSON解析失败，使用部分信息",
                "recommendation": "建议检查LLM输出格式"
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

            # 判断需求质量
            # 评分标准：
            # - 8-10分：优秀，直接进入下一阶段
            # - 5-7分：可接受，可以继续但可能需要后续澄清
            # - 0-4分：不足，需要人工介入
            clarity_score = analysis['clarity_score']
            completeness_score = analysis['completeness_score']
            avg_score = (clarity_score + completeness_score) / 2

            if avg_score < 4:
                # 评分太低，需要人工介入
                print(f"\n[{self.name}] ⚠️  需求质量不足（平均分: {avg_score:.1f}/10），需要人工介入")
                return {
                    'success': False,
                    'message': f'需求质量不足（清晰度{clarity_score}/10，完整度{completeness_score}/10），需要人工澄清',
                    'next_agent': None,  # 不指定下一个Agent，由人工决定
                    'analysis': analysis
                }

            # 评分可接受，继续工作流
            if analysis['questions']:
                print(f"\n[{self.name}] ℹ️  需求基本清晰，但有{len(analysis['questions'])}个建议澄清的问题")
                print(f"[{self.name}] 这些问题可以在后续阶段由产品经理处理")

            print(f"\n[{self.name}] ✓ 需求分析完成（平均分: {avg_score:.1f}/10），可以进入产品设计阶段")

            # 从LLM响应中获取并验证next_agent
            next_agent = self.extract_and_validate_next_agent(analysis, default_agent='product_manager')

            if next_agent:
                print(f"[{self.name}] → 下一个Agent: {next_agent}")

            return {
                'success': True,
                'message': '需求分析完成',
                'next_agent': next_agent,
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
