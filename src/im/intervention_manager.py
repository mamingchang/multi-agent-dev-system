"""
人工介入管理器

实现3级人工介入机制
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

from ..database.models import InterventionRequest, User, Task


class InterventionLevel(str, Enum):
    """
    人工介入级别

    为什么: 根据问题严重程度分级处理
    """
    LEVEL_1 = "level_1"  # 轻度介入：Agent请求确认
    LEVEL_2 = "level_2"  # 中度介入：Agent遇到困难需要指导
    LEVEL_3 = "level_3"  # 重度介入：Agent无法继续，需要人工接管


class InterventionStatus(str, Enum):
    """介入状态"""
    PENDING = "pending"  # 等待处理
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CANCELLED = "cancelled"  # 已取消


class InterventionManager:
    """人工介入管理器"""

    def __init__(self, db: Session):
        self.db = db

    def request_intervention(
        self,
        task_id: int,
        agent_name: str,
        level: InterventionLevel,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
        suggested_actions: Optional[List[str]] = None
    ) -> InterventionRequest:
        """
        请求人工介入

        为什么: Agent遇到问题时主动请求人工帮助
        """
        # 创建介入请求
        request = InterventionRequest(
            task_id=task_id,
            agent_name=agent_name,
            level=level.value,
            reason=reason,
            context=context or {},
            suggested_actions=suggested_actions or [],
            status=InterventionStatus.PENDING.value,
            requested_at=datetime.utcnow()
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)

        # 发送通知
        self._notify_intervention_request(request)

        return request

    def _notify_intervention_request(self, request: InterventionRequest):
        """
        通知人工介入请求

        为什么: 及时通知相关人员处理
        """
        # 根据级别选择通知方式
        if request.level == InterventionLevel.LEVEL_3.value:
            # 重度介入：立即通知所有管理员
            self._send_urgent_notification(request)
        elif request.level == InterventionLevel.LEVEL_2.value:
            # 中度介入：通知项目负责人
            self._send_normal_notification(request)
        else:
            # 轻度介入：仅记录，不主动通知
            pass

    def _send_urgent_notification(self, request: InterventionRequest):
        """发送紧急通知"""
        # TODO: 集成通知系统（邮件、短信、电话等）
        print(f"[URGENT] Intervention request #{request.id}: {request.reason}")

    def _send_normal_notification(self, request: InterventionRequest):
        """发送普通通知"""
        # TODO: 集成通知系统
        print(f"[NOTICE] Intervention request #{request.id}: {request.reason}")

    def assign_intervention(
        self,
        request_id: int,
        assignee_id: int
    ) -> InterventionRequest:
        """
        分配介入请求给人工处理

        为什么: 指定负责人处理介入请求
        """
        request = self.db.query(InterventionRequest).filter(
            InterventionRequest.id == request_id
        ).first()

        if not request:
            raise ValueError(f"Intervention request {request_id} not found")

        request.assigned_to = assignee_id
        request.status = InterventionStatus.IN_PROGRESS.value
        request.assigned_at = datetime.utcnow()

        self.db.commit()
        return request

    def provide_guidance(
        self,
        request_id: int,
        user_id: int,
        guidance: str,
        actions: Optional[List[str]] = None
    ) -> InterventionRequest:
        """
        提供人工指导

        为什么: 人工给出解决方案或指导意见
        """
        request = self.db.query(InterventionRequest).filter(
            InterventionRequest.id == request_id
        ).first()

        if not request:
            raise ValueError(f"Intervention request {request_id} not found")

        # 记录指导内容
        if not request.context:
            request.context = {}

        if "guidance_history" not in request.context:
            request.context["guidance_history"] = []

        request.context["guidance_history"].append({
            "user_id": user_id,
            "guidance": guidance,
            "actions": actions or [],
            "provided_at": datetime.utcnow().isoformat()
        })

        # 更新状态
        request.status = InterventionStatus.RESOLVED.value
        request.resolved_at = datetime.utcnow()
        request.resolution = guidance

        self.db.commit()
        return request

    def cancel_intervention(
        self,
        request_id: int,
        reason: Optional[str] = None
    ) -> InterventionRequest:
        """
        取消介入请求

        为什么: Agent自行解决问题或请求不再需要
        """
        request = self.db.query(InterventionRequest).filter(
            InterventionRequest.id == request_id
        ).first()

        if not request:
            raise ValueError(f"Intervention request {request_id} not found")

        request.status = InterventionStatus.CANCELLED.value
        if reason:
            request.resolution = f"Cancelled: {reason}"

        self.db.commit()
        return request

    def get_pending_interventions(
        self,
        level: Optional[InterventionLevel] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取待处理的介入请求

        为什么: 显示需要人工处理的请求列表
        """
        query = self.db.query(InterventionRequest, Task).join(
            Task, InterventionRequest.task_id == Task.id
        ).filter(
            InterventionRequest.status == InterventionStatus.PENDING.value
        )

        if level:
            query = query.filter(InterventionRequest.level == level.value)

        query = query.order_by(
            InterventionRequest.requested_at.desc()
        ).limit(limit)

        requests = query.all()

        return [
            {
                "id": req.id,
                "task": {
                    "id": task.id,
                    "title": task.title
                },
                "agent_name": req.agent_name,
                "level": req.level,
                "reason": req.reason,
                "context": req.context,
                "suggested_actions": req.suggested_actions,
                "requested_at": req.requested_at.isoformat()
            }
            for req, task in requests
        ]

    def get_intervention_stats(
        self,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取介入统计信息

        为什么: 分析人工介入频率和模式
        """
        query = self.db.query(InterventionRequest)

        if task_id:
            query = query.filter(InterventionRequest.task_id == task_id)

        total = query.count()
        pending = query.filter(
            InterventionRequest.status == InterventionStatus.PENDING.value
        ).count()
        resolved = query.filter(
            InterventionRequest.status == InterventionStatus.RESOLVED.value
        ).count()

        # 按级别统计
        level_stats = {}
        for level in InterventionLevel:
            count = query.filter(
                InterventionRequest.level == level.value
            ).count()
            level_stats[level.value] = count

        return {
            "total": total,
            "pending": pending,
            "resolved": resolved,
            "cancelled": total - pending - resolved,
            "by_level": level_stats
        }
