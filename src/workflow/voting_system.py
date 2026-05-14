"""
Agent协商投票系统

提供Agent之间的协商和投票机制：
- 加权投票（不同Agent权重不同）
- 多轮投票（达成共识）
- 冲突解决（LLM分析+人工介入）
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class VoteOption(str, Enum):
    """投票选项"""
    APPROVE = "approve"      # 同意
    REJECT = "reject"        # 反对
    ABSTAIN = "abstain"      # 弃权
    CONDITIONAL = "conditional"  # 有条件同意


@dataclass
class Vote:
    """
    投票记录

    Attributes:
        agent_name: 投票Agent名称
        option: 投票选项
        reason: 投票理由
        conditions: 条件（如果是conditional）
        weight: 投票权重
    """
    agent_name: str
    option: VoteOption
    reason: str
    conditions: Optional[List[str]] = None
    weight: float = 1.0


@dataclass
class VotingResult:
    """
    投票结果

    Attributes:
        passed: 是否通过
        approve_score: 同意得分
        reject_score: 反对得分
        abstain_count: 弃权数
        votes: 所有投票记录
        consensus_level: 共识程度（0-1）
        conflicts: 冲突列表
    """
    passed: bool
    approve_score: float
    reject_score: float
    abstain_count: int
    votes: List[Vote]
    consensus_level: float
    conflicts: List[str]


class VotingSystem:
    """
    Agent投票系统

    功能：
    1. 加权投票（不同Agent权重不同）
    2. 计算投票结果
    3. 识别冲突
    4. 多轮投票达成共识

    Why:
    - 民主决策：让多个Agent参与决策，避免单点错误
    - 专业权重：重要决策由专业Agent主导
    - 冲突解决：识别分歧，寻求共识或升级人工

    How to apply:
    - 关键决策点（架构选型、技术方案）发起投票
    - 收集各Agent意见
    - 计算加权结果
    - 如果有冲突，进行多轮投票或人工介入

    Example:
        voting = VotingSystem()
        voting.set_agent_weight("Architect", 3.0)  # 架构师权重高
        voting.set_agent_weight("Developer", 2.0)
        voting.set_agent_weight("Tester", 1.5)

        voting.add_vote("Architect", VoteOption.APPROVE, "技术方案可行")
        voting.add_vote("Developer", VoteOption.CONDITIONAL, "需要考虑性能", ["添加缓存"])
        voting.add_vote("Tester", VoteOption.REJECT, "测试覆盖不足")

        result = voting.calculate_result()
        if not result.passed:
            # 处理冲突或升级人工
    """

    # 默认Agent权重
    DEFAULT_WEIGHTS = {
        "Requester": 2.0,        # 需求分析师：理解需求
        "ProductManager": 2.5,   # 产品经理：用户价值
        "Architect": 3.0,        # 架构师：技术决策权重最高
        "Developer": 2.0,        # 开发者：实现可行性
        "CodeReviewer": 2.0,     # 代码审查：代码质量
        "Tester": 1.5,           # 测试：质量保证
        "DevOps": 1.5,           # 运维：部署和稳定性
    }

    def __init__(self, threshold: float = 0.6):
        """
        初始化投票系统

        Args:
            threshold: 通过阈值（0-1），默认0.6表示60%同意即通过

        Why: 可配置的阈值适应不同决策的重要程度
        """
        self.threshold = threshold
        self.agent_weights: Dict[str, float] = self.DEFAULT_WEIGHTS.copy()
        self.votes: List[Vote] = []

    def set_agent_weight(self, agent_name: str, weight: float):
        """
        设置Agent权重

        Args:
            agent_name: Agent名称
            weight: 权重值（建议1.0-3.0）

        Why: 根据决策类型调整Agent权重，例如架构决策时Architect权重更高
        """
        self.agent_weights[agent_name] = weight

    def add_vote(
        self,
        agent_name: str,
        option: VoteOption,
        reason: str,
        conditions: Optional[List[str]] = None
    ):
        """
        添加投票

        Args:
            agent_name: 投票Agent名称
            option: 投票选项
            reason: 投票理由
            conditions: 条件（如果是conditional）

        Why: 记录每个Agent的意见和理由，便于分析和解决冲突
        """
        weight = self.agent_weights.get(agent_name, 1.0)

        vote = Vote(
            agent_name=agent_name,
            option=option,
            reason=reason,
            conditions=conditions,
            weight=weight
        )

        self.votes.append(vote)

    def calculate_result(self) -> VotingResult:
        """
        计算投票结果

        Returns:
            投票结果

        Why: 综合所有投票，计算加权结果，判断是否通过

        Algorithm:
        1. 计算同意得分 = sum(approve权重) + 0.5 * sum(conditional权重)
        2. 计算反对得分 = sum(reject权重)
        3. 计算总权重 = sum(所有非弃权投票权重)
        4. 通过率 = 同意得分 / 总权重
        5. 如果通过率 >= threshold，则通过
        """
        approve_score = 0.0
        reject_score = 0.0
        abstain_count = 0
        total_weight = 0.0

        for vote in self.votes:
            if vote.option == VoteOption.APPROVE:
                approve_score += vote.weight
                total_weight += vote.weight
            elif vote.option == VoteOption.REJECT:
                reject_score += vote.weight
                total_weight += vote.weight
            elif vote.option == VoteOption.CONDITIONAL:
                # 有条件同意算0.5权重
                approve_score += vote.weight * 0.5
                total_weight += vote.weight
            elif vote.option == VoteOption.ABSTAIN:
                abstain_count += 1

        # 计算通过率
        if total_weight > 0:
            approval_rate = approve_score / total_weight
            passed = approval_rate >= self.threshold
        else:
            # 全部弃权，不通过
            passed = False
            approval_rate = 0.0

        # 计算共识程度（0-1，越高表示意见越一致）
        if total_weight > 0:
            # 共识 = 1 - (反对得分 / 总权重)
            consensus_level = 1.0 - (reject_score / total_weight)
        else:
            consensus_level = 0.0

        # 识别冲突
        conflicts = self._identify_conflicts()

        return VotingResult(
            passed=passed,
            approve_score=approve_score,
            reject_score=reject_score,
            abstain_count=abstain_count,
            votes=self.votes.copy(),
            consensus_level=consensus_level,
            conflicts=conflicts
        )

    def _identify_conflicts(self) -> List[str]:
        """
        识别冲突

        Returns:
            冲突描述列表

        Why: 明确指出分歧点，便于针对性解决

        Rules:
        - 如果有高权重Agent反对，记录冲突
        - 如果同意和反对得分接近，记录冲突
        """
        conflicts = []

        # 检查高权重Agent的反对
        for vote in self.votes:
            if vote.option == VoteOption.REJECT and vote.weight >= 2.0:
                conflicts.append(f"{vote.agent_name}（权重{vote.weight}）反对：{vote.reason}")

        # 检查有条件同意
        conditional_votes = [v for v in self.votes if v.option == VoteOption.CONDITIONAL]
        if conditional_votes:
            for vote in conditional_votes:
                conditions_str = "、".join(vote.conditions) if vote.conditions else "无"
                conflicts.append(f"{vote.agent_name}有条件同意，条件：{conditions_str}")

        return conflicts

    def reset(self):
        """
        重置投票

        Why: 支持多轮投票，清空上一轮结果
        """
        self.votes.clear()

    def get_summary(self) -> str:
        """
        获取投票摘要（文本格式）

        Returns:
            投票摘要

        Why: 便于展示给用户或记录到日志
        """
        result = self.calculate_result()

        lines = [
            "投票结果摘要",
            "=" * 50,
            f"是否通过：{'✅ 通过' if result.passed else '❌ 未通过'}",
            f"同意得分：{result.approve_score:.2f}",
            f"反对得分：{result.reject_score:.2f}",
            f"弃权数量：{result.abstain_count}",
            f"共识程度：{result.consensus_level:.1%}",
            "",
            "详细投票：",
        ]

        for vote in result.votes:
            option_emoji = {
                VoteOption.APPROVE: "✅",
                VoteOption.REJECT: "❌",
                VoteOption.CONDITIONAL: "⚠️",
                VoteOption.ABSTAIN: "⏸️"
            }
            emoji = option_emoji.get(vote.option, "")
            lines.append(f"  {emoji} {vote.agent_name}（权重{vote.weight}）：{vote.reason}")

        if result.conflicts:
            lines.append("")
            lines.append("冲突点：")
            for conflict in result.conflicts:
                lines.append(f"  ⚠️ {conflict}")

        lines.append("=" * 50)

        return "\n".join(lines)


class ConflictResolver:
    """
    冲突解决器

    功能：
    1. 分析冲突原因
    2. 提出解决方案
    3. 组织多轮投票
    4. 升级人工介入

    Why: 自动化冲突解决流程，减少人工介入次数

    How to apply:
    - 投票未通过时，调用冲突解决器
    - 分析冲突原因
    - 尝试自动解决（如满足条件）
    - 如果无法解决，升级人工
    """

    def __init__(self, llm_client=None):
        """
        初始化冲突解决器

        Args:
            llm_client: LLM客户端（用于分析冲突）
        """
        self.llm_client = llm_client

    async def analyze_conflict(self, voting_result: VotingResult) -> Dict[str, Any]:
        """
        分析冲突

        Args:
            voting_result: 投票结果

        Returns:
            冲突分析结果

        Why: 理解冲突本质，找到解决方向
        """
        if not voting_result.conflicts:
            return {
                "has_conflict": False,
                "analysis": "无冲突",
                "suggestions": []
            }

        # 如果有LLM，使用LLM分析
        if self.llm_client:
            return await self._llm_analyze_conflict(voting_result)

        # 否则使用规则分析
        return self._rule_based_analyze(voting_result)

    def _rule_based_analyze(self, voting_result: VotingResult) -> Dict[str, Any]:
        """
        基于规则的冲突分析

        Args:
            voting_result: 投票结果

        Returns:
            分析结果
        """
        suggestions = []

        # 检查有条件同意
        conditional_votes = [v for v in voting_result.votes if v.option == VoteOption.CONDITIONAL]
        if conditional_votes:
            all_conditions = []
            for vote in conditional_votes:
                if vote.conditions:
                    all_conditions.extend(vote.conditions)

            suggestions.append({
                "type": "满足条件",
                "description": f"满足以下条件后重新投票：{', '.join(all_conditions)}"
            })

        # 检查反对票
        reject_votes = [v for v in voting_result.votes if v.option == VoteOption.REJECT]
        if reject_votes:
            suggestions.append({
                "type": "解决反对意见",
                "description": f"需要解决{len(reject_votes)}个反对意见"
            })

        # 如果共识程度低，建议人工介入
        if voting_result.consensus_level < 0.5:
            suggestions.append({
                "type": "人工介入",
                "description": "共识程度较低，建议人工裁决"
            })

        return {
            "has_conflict": True,
            "analysis": f"发现{len(voting_result.conflicts)}个冲突点",
            "suggestions": suggestions
        }

    async def _llm_analyze_conflict(self, voting_result: VotingResult) -> Dict[str, Any]:
        """
        使用LLM分析冲突

        Args:
            voting_result: 投票结果

        Returns:
            分析结果
        """
        # 构建prompt
        votes_text = "\n".join([
            f"- {v.agent_name}：{v.option.value}，理由：{v.reason}"
            for v in voting_result.votes
        ])

        prompt = f"""
分析以下Agent投票冲突：

{votes_text}

请分析：
1. 冲突的根本原因是什么？
2. 各方的核心关注点是什么？
3. 有哪些可能的解决方案？
4. 是否需要人工介入？

请给出简洁的分析和建议。
"""

        try:
            response = await self.llm_client.generate(prompt)
            return {
                "has_conflict": True,
                "analysis": response,
                "suggestions": []  # 从LLM响应中提取
            }
        except Exception as e:
            print(f"LLM分析失败: {e}")
            return self._rule_based_analyze(voting_result)
