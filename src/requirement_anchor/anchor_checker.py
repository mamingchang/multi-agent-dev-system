"""
需求锚点检查系统

检查需求偏离，确保开发符合原始需求
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class RequirementLevel(str, Enum):
    """需求层级"""
    BUSINESS = "business"  # 业务需求
    FUNCTIONAL = "functional"  # 功能需求
    TECHNICAL = "technical"  # 技术需求


class DeviationType(str, Enum):
    """偏离类型"""
    SCOPE_CREEP = "scope_creep"  # 范围蔓延
    REQUIREMENT_CHANGE = "requirement_change"  # 需求变更
    TECHNICAL_DRIFT = "technical_drift"  # 技术偏离


class RequirementAnchor:
    """
    需求锚点检查器

    为什么: 防止开发过程中偏离原始需求
    """

    def __init__(self, db):
        self.db = db

    def create_anchor(
        self,
        project_id: int,
        level: RequirementLevel,
        description: str,
        acceptance_criteria: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建需求锚点

        为什么: 记录原始需求作为基准
        """
        from ..database.models import RequirementAnchor as AnchorModel
        import hashlib

        # 生成锚点ID
        anchor_id = hashlib.sha256(
            f"{project_id}_{level}_{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]

        anchor = AnchorModel(
            anchor_id=anchor_id,
            project_id=project_id,
            level=level.value,
            description=description,
            acceptance_criteria=acceptance_criteria,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        self.db.add(anchor)
        self.db.commit()

        return anchor_id

    def check_deviation(
        self,
        anchor_id: str,
        current_implementation: str,
        current_features: List[str]
    ) -> Dict[str, Any]:
        """
        检查偏离

        为什么: 对比当前实现与原始需求
        """
        from ..database.models import RequirementAnchor as AnchorModel

        anchor = self.db.query(AnchorModel).filter(
            AnchorModel.anchor_id == anchor_id
        ).first()

        if not anchor:
            return {"error": "Anchor not found"}

        # 检查接受标准是否满足
        criteria_met = []
        criteria_unmet = []

        for criterion in anchor.acceptance_criteria:
            # 简单的关键词匹配（实际应该用LLM分析）
            if any(keyword.lower() in current_implementation.lower()
                   for keyword in criterion.split()):
                criteria_met.append(criterion)
            else:
                criteria_unmet.append(criterion)

        # 检查范围蔓延
        extra_features = [f for f in current_features
                         if f not in anchor.acceptance_criteria]

        # 计算偏离程度
        deviation_score = len(criteria_unmet) / len(anchor.acceptance_criteria) \
            if anchor.acceptance_criteria else 0

        result = {
            "anchor_id": anchor_id,
            "level": anchor.level,
            "original_description": anchor.description,
            "criteria_met": criteria_met,
            "criteria_unmet": criteria_unmet,
            "extra_features": extra_features,
            "deviation_score": round(deviation_score, 2),
            "has_deviation": deviation_score > 0.2 or len(extra_features) > 0,
            "checked_at": datetime.utcnow().isoformat()
        }

        # 记录检查结果
        self._record_check(anchor_id, result)

        return result

    def _record_check(self, anchor_id: str, result: Dict[str, Any]):
        """
        记录检查结果

        为什么: 保存检查历史
        """
        from ..database.models import RequirementCheck

        check = RequirementCheck(
            anchor_id=anchor_id,
            deviation_score=result["deviation_score"],
            has_deviation=result["has_deviation"],
            check_result=result,
            checked_at=datetime.utcnow()
        )

        self.db.add(check)
        self.db.commit()

    def get_anchor_history(self, anchor_id: str) -> List[Dict[str, Any]]:
        """
        获取锚点检查历史

        为什么: 查看需求偏离趋势
        """
        from ..database.models import RequirementCheck

        checks = self.db.query(RequirementCheck).filter(
            RequirementCheck.anchor_id == anchor_id
        ).order_by(RequirementCheck.checked_at.desc()).all()

        return [
            {
                "deviation_score": c.deviation_score,
                "has_deviation": c.has_deviation,
                "checked_at": c.checked_at.isoformat()
            }
            for c in checks
        ]

    def list_anchors(
        self,
        project_id: int,
        level: Optional[RequirementLevel] = None
    ) -> List[Dict[str, Any]]:
        """
        列出项目的需求锚点

        为什么: 查看所有需求基准
        """
        from ..database.models import RequirementAnchor as AnchorModel

        query = self.db.query(AnchorModel).filter(
            AnchorModel.project_id == project_id
        )

        if level:
            query = query.filter(AnchorModel.level == level.value)

        anchors = query.all()

        return [
            {
                "anchor_id": a.anchor_id,
                "level": a.level,
                "description": a.description,
                "criteria_count": len(a.acceptance_criteria),
                "created_at": a.created_at.isoformat()
            }
            for a in anchors
        ]
