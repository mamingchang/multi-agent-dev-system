"""
产物版本管理服务

提供版本号生成、版本对比、版本回滚等功能。

版本号格式：v{YYYYMMDD}_{HHMMSS}[_{序号}]
例如：v20260509_143022, v20260509_143022_1
"""

import difflib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from ..database.models import Artifact, Task


class VersionGenerator:
    """版本号生成器"""

    @staticmethod
    def generate_version(base_time: Optional[datetime] = None) -> str:
        """
        生成版本号

        Args:
            base_time: 基准时间，默认为当前时间

        Returns:
            str: 版本号
        """
        if base_time is None:
            base_time = datetime.utcnow()

        return f"v{base_time.strftime('%Y%m%d_%H%M%S')}"

    @staticmethod
    def generate_unique_version(
        session: Session,
        task_id: str,
        artifact_name: str,
        base_time: Optional[datetime] = None
    ) -> str:
        """
        生成唯一版本号

        如果同一秒内有多个版本，添加序号后缀。

        Args:
            session: 数据库会话
            task_id: 任务ID
            artifact_name: 产物名称
            base_time: 基准时间

        Returns:
            str: 唯一版本号
        """
        base_version = VersionGenerator.generate_version(base_time)

        # 检查是否已存在
        existing = session.query(Artifact).filter(
            Artifact.task_id == task_id,
            Artifact.name == artifact_name,
            Artifact.version.like(f"{base_version}%")
        ).all()

        if not existing:
            return base_version

        # 存在同名版本，添加序号
        max_seq = 0
        for artifact in existing:
            if artifact.version == base_version:
                max_seq = max(max_seq, 0)
            elif artifact.version.startswith(f"{base_version}_"):
                try:
                    seq = int(artifact.version.split("_")[-1])
                    max_seq = max(max_seq, seq)
                except ValueError:
                    pass

        return f"{base_version}_{max_seq + 1}"


class VersionComparator:
    """版本对比器"""

    @staticmethod
    def diff_text(old_content: str, new_content: str) -> Dict[str, Any]:
        """
        对比两个文本版本

        Args:
            old_content: 旧版本内容
            new_content: 新版本内容

        Returns:
            dict: 对比结果
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # 生成unified diff
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            fromfile='old',
            tofile='new'
        ))

        # 统计变更
        added_lines = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        changed_lines = min(added_lines, removed_lines)

        return {
            "diff": ''.join(diff),
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "changed_lines": changed_lines,
            "total_changes": added_lines + removed_lines
        }

    @staticmethod
    def generate_semantic_description(
        old_content: str,
        new_content: str,
        diff_result: Dict[str, Any]
    ) -> str:
        """
        生成语义化的变更描述

        Args:
            old_content: 旧版本内容
            new_content: 新版本内容
            diff_result: diff结果

        Returns:
            str: 语义描述
        """
        # 简单的语义描述生成
        # 实际使用时可以调用LLM生成更详细的描述

        if diff_result["total_changes"] == 0:
            return "无变更"

        parts = []

        if diff_result["added_lines"] > 0:
            parts.append(f"新增 {diff_result['added_lines']} 行")

        if diff_result["removed_lines"] > 0:
            parts.append(f"删除 {diff_result['removed_lines']} 行")

        if diff_result["changed_lines"] > 0:
            parts.append(f"修改 {diff_result['changed_lines']} 行")

        return "、".join(parts)


class VersionManager:
    """版本管理器"""

    def __init__(self, session: Session):
        """
        初始化版本管理器

        Args:
            session: 数据库会话
        """
        self.session = session

    def create_version(
        self,
        task_id: str,
        artifact_name: str,
        artifact_type: str,
        content: str,
        parent_version: Optional[str] = None,
        is_key_version: bool = False,
        version_description: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Artifact:
        """
        创建新版本

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            artifact_type: 产物类型
            content: 内容
            parent_version: 父版本号
            is_key_version: 是否为关键版本
            version_description: 版本描述
            created_by: 创建者ID

        Returns:
            Artifact: 创建的产物
        """
        # 生成版本号
        version = VersionGenerator.generate_unique_version(
            self.session,
            task_id,
            artifact_name
        )

        # 创建产物
        artifact = Artifact(
            task_id=task_id,
            name=artifact_name,
            artifact_type=artifact_type,
            content=content,
            version=version,
            parent_version=parent_version,
            is_key_version=is_key_version,
            version_description=version_description,
            created_by=created_by
        )

        self.session.add(artifact)
        self.session.commit()
        self.session.refresh(artifact)

        print(f"创建版本: {artifact_name} {version}")

        return artifact

    def get_version(
        self,
        task_id: str,
        artifact_name: str,
        version: str
    ) -> Optional[Artifact]:
        """
        获取指定版本

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            version: 版本号

        Returns:
            Optional[Artifact]: 产物对象
        """
        return self.session.query(Artifact).filter(
            Artifact.task_id == task_id,
            Artifact.name == artifact_name,
            Artifact.version == version
        ).first()

    def list_versions(
        self,
        task_id: str,
        artifact_name: str,
        key_versions_only: bool = False
    ) -> List[Artifact]:
        """
        列出所有版本

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            key_versions_only: 只返回关键版本

        Returns:
            List[Artifact]: 版本列表
        """
        query = self.session.query(Artifact).filter(
            Artifact.task_id == task_id,
            Artifact.name == artifact_name
        )

        if key_versions_only:
            query = query.filter(Artifact.is_key_version == True)

        return query.order_by(Artifact.created_at.desc()).all()

    def compare_versions(
        self,
        task_id: str,
        artifact_name: str,
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """
        对比两个版本

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            from_version: 起始版本
            to_version: 目标版本

        Returns:
            dict: 对比结果
        """
        # 获取两个版本
        old_artifact = self.get_version(task_id, artifact_name, from_version)
        new_artifact = self.get_version(task_id, artifact_name, to_version)

        if not old_artifact or not new_artifact:
            raise ValueError("版本不存在")

        # 对比内容
        diff_result = VersionComparator.diff_text(
            old_artifact.content or "",
            new_artifact.content or ""
        )

        # 生成语义描述
        semantic_description = VersionComparator.generate_semantic_description(
            old_artifact.content or "",
            new_artifact.content or "",
            diff_result
        )

        return {
            "from_version": from_version,
            "to_version": to_version,
            "diff": diff_result["diff"],
            "added_lines": diff_result["added_lines"],
            "removed_lines": diff_result["removed_lines"],
            "changed_lines": diff_result["changed_lines"],
            "total_changes": diff_result["total_changes"],
            "semantic_description": semantic_description
        }

    def mark_as_key_version(
        self,
        task_id: str,
        artifact_name: str,
        version: str,
        description: Optional[str] = None
    ) -> bool:
        """
        标记为关键版本

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            version: 版本号
            description: 版本描述

        Returns:
            bool: 是否成功
        """
        artifact = self.get_version(task_id, artifact_name, version)

        if not artifact:
            return False

        artifact.is_key_version = True
        if description:
            artifact.version_description = description

        self.session.commit()

        print(f"标记关键版本: {artifact_name} {version}")

        return True

    def rollback_to_version(
        self,
        task_id: str,
        artifact_name: str,
        target_version: str
    ) -> Artifact:
        """
        回滚到指定版本

        创建一个新版本，内容与目标版本相同。

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            target_version: 目标版本号

        Returns:
            Artifact: 新创建的版本
        """
        # 获取目标版本
        target_artifact = self.get_version(task_id, artifact_name, target_version)

        if not target_artifact:
            raise ValueError(f"目标版本不存在: {target_version}")

        # 创建新版本（内容与目标版本相同）
        new_artifact = self.create_version(
            task_id=task_id,
            artifact_name=artifact_name,
            artifact_type=target_artifact.artifact_type,
            content=target_artifact.content,
            parent_version=target_version,
            version_description=f"回滚到版本 {target_version}"
        )

        print(f"回滚版本: {artifact_name} {target_version} -> {new_artifact.version}")

        return new_artifact

    def cleanup_old_versions(
        self,
        task_id: str,
        artifact_name: str,
        keep_days: int = 30
    ) -> int:
        """
        清理旧版本

        保留关键版本和最近N天的版本。

        Args:
            task_id: 任务ID
            artifact_name: 产物名称
            keep_days: 保留天数

        Returns:
            int: 删除的版本数
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

        # 查询要删除的版本（非关键版本且超过保留期）
        to_delete = self.session.query(Artifact).filter(
            Artifact.task_id == task_id,
            Artifact.name == artifact_name,
            Artifact.is_key_version == False,
            Artifact.created_at < cutoff_date
        ).all()

        count = len(to_delete)

        for artifact in to_delete:
            self.session.delete(artifact)

        self.session.commit()

        print(f"清理旧版本: {artifact_name}, 删除 {count} 个版本")

        return count
