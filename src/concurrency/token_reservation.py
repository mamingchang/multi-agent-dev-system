"""
Token预留机制

在任务执行前预估和预留Token，防止配额耗尽。

预留流程：
1. 预估：根据任务描述、历史统计、Agent类型预估Token消耗
2. 预留：从组织配额中预留Token
3. 执行：任务执行过程中实际消耗Token
4. 释放：任务完成后释放未使用的预留Token
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..database.models import Organization, Task
from ..database.organization_repository import OrganizationRepository
from ..database.quota_repository import QuotaUsageRepository
from ..exceptions import QuotaInsufficientException


class TokenReservation:
    """Token预留记录"""

    def __init__(
        self,
        task_id: str,
        organization_id: int,
        reserved_tokens: int,
        estimated_tokens: int
    ):
        """
        初始化预留记录

        Args:
            task_id: 任务ID
            organization_id: 组织ID
            reserved_tokens: 预留的Token数
            estimated_tokens: 预估的Token数
        """
        self.task_id = task_id
        self.organization_id = organization_id
        self.reserved_tokens = reserved_tokens
        self.estimated_tokens = estimated_tokens
        self.actual_tokens = 0
        self.created_at = datetime.utcnow()
        self.released = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "organization_id": self.organization_id,
            "reserved_tokens": self.reserved_tokens,
            "estimated_tokens": self.estimated_tokens,
            "actual_tokens": self.actual_tokens,
            "released": self.released,
            "created_at": self.created_at.isoformat()
        }


class TokenEstimator:
    """
    Token预估器

    根据任务信息预估Token消耗。
    """

    # 基础Token消耗（每个Agent的平均消耗）
    BASE_TOKENS_PER_AGENT = {
        "ProductManager": 2000,
        "Architect": 3000,
        "Developer": 5000,
        "Tester": 2000,
        "CodeReviewer": 2000,
        "DevOpsEngineer": 1500,
        "Deployer": 1000
    }

    # 任务复杂度系数
    COMPLEXITY_MULTIPLIER = {
        "simple": 0.5,
        "medium": 1.0,
        "complex": 2.0,
        "very_complex": 3.0
    }

    @staticmethod
    def estimate_tokens(
        task_description: str,
        agent_sequence: list = None,
        complexity: str = "medium"
    ) -> int:
        """
        预估任务的Token消耗

        Args:
            task_description: 任务描述
            agent_sequence: Agent执行序列
            complexity: 任务复杂度

        Returns:
            int: 预估的Token数
        """
        # 基础预估：根据描述长度
        base_estimate = len(task_description) * 10  # 每个字符约10个Token

        # 如果指定了Agent序列，累加每个Agent的预估消耗
        if agent_sequence:
            agent_estimate = sum(
                TokenEstimator.BASE_TOKENS_PER_AGENT.get(agent, 2000)
                for agent in agent_sequence
            )
        else:
            # 默认假设使用所有Agent
            agent_estimate = sum(TokenEstimator.BASE_TOKENS_PER_AGENT.values())

        # 应用复杂度系数
        multiplier = TokenEstimator.COMPLEXITY_MULTIPLIER.get(complexity, 1.0)

        # 总预估 = (基础预估 + Agent预估) * 复杂度系数
        total_estimate = int((base_estimate + agent_estimate) * multiplier)

        # 添加20%的缓冲
        return int(total_estimate * 1.2)


class TokenReservationManager:
    """
    Token预留管理器

    管理所有任务的Token预留。
    """

    def __init__(self):
        """初始化管理器"""
        self.reservations: Dict[str, TokenReservation] = {}

    def reserve_tokens(
        self,
        session: Session,
        task_id: str,
        organization_id: int,
        estimated_tokens: int
    ) -> TokenReservation:
        """
        预留Token

        Args:
            session: 数据库会话
            task_id: 任务ID
            organization_id: 组织ID
            estimated_tokens: 预估的Token数

        Returns:
            TokenReservation: 预留记录

        Raises:
            QuotaInsufficientException: 如果配额不足
        """
        # 检查组织配额
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_id(organization_id)

        if not org:
            raise ValueError(f"组织不存在: {organization_id}")

        # 计算可用配额
        available = org.token_quota - org.token_used

        # 检查是否足够
        if estimated_tokens > available:
            raise QuotaInsufficientException(
                organization_id=organization_id,
                required=estimated_tokens,
                available=available
            )

        # 创建预留记录
        reservation = TokenReservation(
            task_id=task_id,
            organization_id=organization_id,
            reserved_tokens=estimated_tokens,
            estimated_tokens=estimated_tokens
        )

        # 更新组织的已使用配额（预留）
        org.token_used += estimated_tokens
        session.commit()

        # 保存预留记录
        self.reservations[task_id] = reservation

        print(f"Token预留成功: 任务 {task_id}, 预留 {estimated_tokens} tokens")

        return reservation

    def release_tokens(
        self,
        session: Session,
        task_id: str,
        actual_tokens: int
    ):
        """
        释放Token预留

        Args:
            session: 数据库会话
            task_id: 任务ID
            actual_tokens: 实际使用的Token数
        """
        if task_id not in self.reservations:
            print(f"警告: 任务 {task_id} 没有预留记录")
            return

        reservation = self.reservations[task_id]

        if reservation.released:
            print(f"警告: 任务 {task_id} 的预留已经释放")
            return

        # 计算需要释放的Token数
        # 实际使用 < 预留：释放多余的
        # 实际使用 > 预留：需要补充（但不释放）
        tokens_to_release = max(0, reservation.reserved_tokens - actual_tokens)

        # 更新组织配额
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_id(reservation.organization_id)

        if org:
            # 释放未使用的预留
            org.token_used -= tokens_to_release
            session.commit()

        # 更新预留记录
        reservation.actual_tokens = actual_tokens
        reservation.released = True

        print(f"Token预留释放: 任务 {task_id}, 预留 {reservation.reserved_tokens}, "
              f"实际 {actual_tokens}, 释放 {tokens_to_release}")

        # 从管理器中移除
        del self.reservations[task_id]

    def get_reservation(self, task_id: str) -> Optional[TokenReservation]:
        """
        获取预留记录

        Args:
            task_id: 任务ID

        Returns:
            Optional[TokenReservation]: 预留记录
        """
        return self.reservations.get(task_id)

    def get_organization_reserved(self, organization_id: int) -> int:
        """
        获取组织的总预留Token数

        Args:
            organization_id: 组织ID

        Returns:
            int: 总预留Token数
        """
        return sum(
            r.reserved_tokens
            for r in self.reservations.values()
            if r.organization_id == organization_id and not r.released
        )

    def get_all_reservations(self) -> Dict[str, TokenReservation]:
        """
        获取所有预留记录

        Returns:
            dict: 任务ID到预留记录的映射
        """
        return self.reservations.copy()


# 全局Token预留管理器实例
token_reservation_manager = TokenReservationManager()
