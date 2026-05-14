"""
跨项目协作系统

支持项目间共享产物和审批流程
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class ShareStatus(str, Enum):
    """共享状态"""
    PENDING = "pending"  # 待审批
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝


class ArtifactType(str, Enum):
    """产物类型"""
    CODE = "code"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"


class CrossProjectCollaboration:
    """
    跨项目协作管理器

    为什么: 支持团队间的知识和资源共享
    """

    def __init__(self, db):
        self.db = db

    def share_artifact(
        self,
        source_project_id: int,
        artifact_id: str,
        target_project_ids: List[int],
        share_type: ArtifactType,
        description: str,
        shared_by: int
    ) -> str:
        """
        共享产物

        为什么: 将一个项目的产物分享给其他项目
        """
        from ..database.models import SharedArtifact
        import hashlib

        # 生成共享ID
        share_id = hashlib.sha256(
            f"{source_project_id}_{artifact_id}_{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]

        # 创建共享记录
        for target_id in target_project_ids:
            share = SharedArtifact(
                share_id=share_id,
                source_project_id=source_project_id,
                target_project_id=target_id,
                artifact_id=artifact_id,
                share_type=share_type.value,
                description=description,
                status=ShareStatus.PENDING.value,
                shared_by=shared_by,
                shared_at=datetime.utcnow()
            )
            self.db.add(share)

        self.db.commit()
        return share_id

    def approve_share(
        self,
        share_id: str,
        target_project_id: int,
        approved_by: int,
        notes: Optional[str] = None
    ) -> bool:
        """
        批准共享

        为什么: 目标项目审批是否接受共享
        """
        from ..database.models import SharedArtifact

        share = self.db.query(SharedArtifact).filter(
            SharedArtifact.share_id == share_id,
            SharedArtifact.target_project_id == target_project_id
        ).first()

        if not share:
            return False

        share.status = ShareStatus.APPROVED.value
        share.approved_by = approved_by
        share.approved_at = datetime.utcnow()
        share.approval_notes = notes

        self.db.commit()
        return True

    def reject_share(
        self,
        share_id: str,
        target_project_id: int,
        rejected_by: int,
        reason: str
    ) -> bool:
        """
        拒绝共享

        为什么: 目标项目拒绝接受共享
        """
        from ..database.models import SharedArtifact

        share = self.db.query(SharedArtifact).filter(
            SharedArtifact.share_id == share_id,
            SharedArtifact.target_project_id == target_project_id
        ).first()

        if not share:
            return False

        share.status = ShareStatus.REJECTED.value
        share.rejected_by = rejected_by
        share.rejected_at = datetime.utcnow()
        share.rejection_reason = reason

        self.db.commit()
        return True

    def get_pending_approvals(
        self,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取待审批的共享

        为什么: 显示需要审批的共享请求
        """
        from ..database.models import SharedArtifact

        shares = self.db.query(SharedArtifact).filter(
            SharedArtifact.target_project_id == project_id,
            SharedArtifact.status == ShareStatus.PENDING.value
        ).all()

        return [
            {
                "share_id": s.share_id,
                "source_project_id": s.source_project_id,
                "artifact_id": s.artifact_id,
                "share_type": s.share_type,
                "description": s.description,
                "shared_by": s.shared_by,
                "shared_at": s.shared_at.isoformat()
            }
            for s in shares
        ]

    def get_shared_artifacts(
        self,
        project_id: int,
        status: Optional[ShareStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        获取项目的共享产物

        为什么: 查看项目分享或接收的产物
        """
        from ..database.models import SharedArtifact
        from sqlalchemy import or_

        query = self.db.query(SharedArtifact).filter(
            or_(
                SharedArtifact.source_project_id == project_id,
                SharedArtifact.target_project_id == project_id
            )
        )

        if status:
            query = query.filter(SharedArtifact.status == status.value)

        shares = query.order_by(SharedArtifact.shared_at.desc()).all()

        return [
            {
                "share_id": s.share_id,
                "source_project_id": s.source_project_id,
                "target_project_id": s.target_project_id,
                "artifact_id": s.artifact_id,
                "share_type": s.share_type,
                "status": s.status,
                "shared_at": s.shared_at.isoformat()
            }
            for s in shares
        ]

    def get_collaboration_statistics(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取协作统计

        为什么: 了解项目的协作活跃度
        """
        from ..database.models import SharedArtifact
        from sqlalchemy import or_

        # 分享出去的
        shared_out = self.db.query(SharedArtifact).filter(
            SharedArtifact.source_project_id == project_id
        ).count()

        # 接收的
        received = self.db.query(SharedArtifact).filter(
            SharedArtifact.target_project_id == project_id,
            SharedArtifact.status == ShareStatus.APPROVED.value
        ).count()

        # 待审批的
        pending = self.db.query(SharedArtifact).filter(
            SharedArtifact.target_project_id == project_id,
            SharedArtifact.status == ShareStatus.PENDING.value
        ).count()

        return {
            "shared_out": shared_out,
            "received": received,
            "pending_approvals": pending
        }
