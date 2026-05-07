"""
Decision Queue
决策队列管理 - 处理人工Agent的待办决策
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .database.models import PendingDecision, DecisionStatus, Task, User


class DecisionQueue:
    """决策队列管理器"""

    def __init__(self, db_session: Session):
        """
        初始化决策队列

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

    def create_decision(
        self,
        task_id: str,
        agent_name: str,
        decision_type: str,
        context: Dict[str, Any],
        assigned_to: Optional[int] = None
    ) -> PendingDecision:
        """
        创建待办决策

        Args:
            task_id: 任务ID
            agent_name: Agent名称
            decision_type: 决策类型 (approval, review, input)
            context: 决策上下文信息
            assigned_to: 指定处理人用户ID（可选）

        Returns:
            创建的决策对象
        """
        decision = PendingDecision(
            task_id=task_id,
            agent_name=agent_name,
            decision_type=decision_type,
            context=context,
            assigned_to=assigned_to,
            status=DecisionStatus.PENDING
        )
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)

        print(f"✓ 创建决策: {decision.id} - {agent_name} ({decision_type})")
        return decision

    def get_decision(self, decision_id: int) -> Optional[PendingDecision]:
        """获取决策详情"""
        return self.db.query(PendingDecision).filter_by(id=decision_id).first()

    def get_pending_decisions(
        self,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[str] = None
    ) -> List[PendingDecision]:
        """
        获取待处理决策列表

        Args:
            user_id: 用户ID（获取分配给该用户的决策）
            project_id: 项目ID（获取该项目的所有决策）
            task_id: 任务ID（获取该任务的所有决策）

        Returns:
            决策列表
        """
        query = self.db.query(PendingDecision).filter_by(status=DecisionStatus.PENDING)

        if user_id:
            query = query.filter(
                (PendingDecision.assigned_to == user_id) |
                (PendingDecision.assigned_to.is_(None))
            )

        if task_id:
            query = query.filter_by(task_id=task_id)

        if project_id:
            # 通过Task关联到Session再关联到Project
            from .database.models import Session as DBSession
            query = query.join(Task).join(DBSession).filter(
                DBSession.project_id == project_id
            )

        return query.order_by(PendingDecision.created_at).all()

    def resolve_decision(
        self,
        decision_id: int,
        user_id: int,
        response: Dict[str, Any]
    ) -> PendingDecision:
        """
        解决决策

        Args:
            decision_id: 决策ID
            user_id: 处理人用户ID
            response: 决策结果

        Returns:
            更新后的决策对象

        Raises:
            ValueError: 决策不存在或已处理
        """
        decision = self.get_decision(decision_id)
        if not decision:
            raise ValueError(f"决策 {decision_id} 不存在")

        if decision.status != DecisionStatus.PENDING:
            raise ValueError(f"决策 {decision_id} 已处理，状态: {decision.status.value}")

        decision.status = DecisionStatus.RESOLVED
        decision.response = response
        decision.resolved_at = datetime.utcnow()
        decision.resolved_by = user_id

        self.db.commit()
        self.db.refresh(decision)

        print(f"✓ 决策已解决: {decision_id} by user {user_id}")
        return decision

    def cancel_decision(self, decision_id: int) -> bool:
        """
        取消决策

        Args:
            decision_id: 决策ID

        Returns:
            是否成功取消
        """
        decision = self.get_decision(decision_id)
        if not decision:
            return False

        if decision.status != DecisionStatus.PENDING:
            return False

        decision.status = DecisionStatus.CANCELLED
        self.db.commit()
        return True

    def check_timeout(self, decision_id: int, timeout_minutes: int = 60) -> bool:
        """
        检查决策是否超时

        Args:
            decision_id: 决策ID
            timeout_minutes: 超时时间（分钟）

        Returns:
            是否超时
        """
        decision = self.get_decision(decision_id)
        if not decision or decision.status != DecisionStatus.PENDING:
            return False

        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        if decision.created_at < timeout_threshold:
            decision.status = DecisionStatus.TIMEOUT
            self.db.commit()
            print(f"⚠ 决策超时: {decision_id}")
            return True

        return False

    def get_user_decision_history(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户的决策历史

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            决策历史列表
        """
        decisions = self.db.query(PendingDecision).filter_by(
            resolved_by=user_id
        ).order_by(
            PendingDecision.resolved_at.desc()
        ).limit(limit).all()

        history = []
        for decision in decisions:
            task = decision.task
            history.append({
                'decision_id': decision.id,
                'task_id': task.id,
                'task_title': task.title,
                'agent_name': decision.agent_name,
                'decision_type': decision.decision_type,
                'status': decision.status.value,
                'created_at': decision.created_at.isoformat(),
                'resolved_at': decision.resolved_at.isoformat() if decision.resolved_at else None,
                'response': decision.response
            })

        return history

    def get_task_decisions(self, task_id: str) -> List[PendingDecision]:
        """
        获取任务的所有决策

        Args:
            task_id: 任务ID

        Returns:
            决策列表
        """
        return self.db.query(PendingDecision).filter_by(
            task_id=task_id
        ).order_by(PendingDecision.created_at).all()

    def notify_decision_needed(self, decision_id: int) -> None:
        """
        通知决策需要处理（预留接口）

        Args:
            decision_id: 决策ID

        Note:
            实际通知逻辑在notification.py中实现
        """
        decision = self.get_decision(decision_id)
        if not decision:
            return

        # TODO: 集成通知系统
        print(f"📢 通知: 决策 {decision_id} 需要处理")
        if decision.assigned_to:
            print(f"   分配给用户: {decision.assigned_to}")

    def get_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取决策统计信息

        Args:
            project_id: 项目ID（可选）

        Returns:
            统计信息
        """
        query = self.db.query(PendingDecision)

        if project_id:
            from .database.models import Session as DBSession
            query = query.join(Task).join(DBSession).filter(
                DBSession.project_id == project_id
            )

        total = query.count()
        pending = query.filter_by(status=DecisionStatus.PENDING).count()
        resolved = query.filter_by(status=DecisionStatus.RESOLVED).count()
        timeout = query.filter_by(status=DecisionStatus.TIMEOUT).count()
        cancelled = query.filter_by(status=DecisionStatus.CANCELLED).count()

        return {
            'total': total,
            'pending': pending,
            'resolved': resolved,
            'timeout': timeout,
            'cancelled': cancelled,
            'resolution_rate': resolved / total if total > 0 else 0
        }
