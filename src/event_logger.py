"""
Event Logger
事件日志系统 - 记录所有Agent操作，实现完整追溯
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .database.models import TaskEvent, Task


class EventLogger:
    """事件日志记录器"""

    def __init__(self, db_session: Session):
        """
        初始化事件日志记录器

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

    def log_agent_start(
        self,
        task_id: str,
        agent_name: str,
        agent_type: str = 'ai',
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskEvent:
        """
        记录Agent开始执行

        Args:
            task_id: 任务ID
            agent_name: Agent名称
            agent_type: Agent类型 ('ai' or 'human')
            user_id: 用户ID（人工Agent时必填）
            context: 上下文信息

        Returns:
            事件对象
        """
        event = TaskEvent(
            task_id=task_id,
            agent_name=agent_name,
            agent_type=agent_type,
            event_type='start',
            content={
                'context': context or {},
                'started_at': datetime.utcnow().isoformat()
            },
            created_by_user=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def log_agent_complete(
        self,
        task_id: str,
        agent_name: str,
        result: Dict[str, Any],
        duration: Optional[float] = None,
        user_id: Optional[int] = None
    ) -> TaskEvent:
        """
        记录Agent完成执行

        Args:
            task_id: 任务ID
            agent_name: Agent名称
            result: 执行结果
            duration: 执行时长（秒）
            user_id: 用户ID（人工Agent时必填）

        Returns:
            事件对象
        """
        event = TaskEvent(
            task_id=task_id,
            agent_name=agent_name,
            agent_type='human' if user_id else 'ai',
            event_type='complete',
            content={
                'result': result,
                'duration': duration,
                'completed_at': datetime.utcnow().isoformat()
            },
            created_by_user=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def log_artifact_created(
        self,
        task_id: str,
        artifact_type: str,
        content: Any,
        created_by: str,
        user_id: Optional[int] = None
    ) -> TaskEvent:
        """
        记录产物创建

        Args:
            task_id: 任务ID
            artifact_type: 产物类型
            content: 产物内容
            created_by: 创建者（Agent名称）
            user_id: 用户ID（人工创建时）

        Returns:
            事件对象
        """
        event = TaskEvent(
            task_id=task_id,
            agent_name=created_by,
            agent_type='human' if user_id else 'ai',
            event_type='artifact',
            content={
                'artifact_type': artifact_type,
                'content': content,
                'created_at': datetime.utcnow().isoformat()
            },
            created_by_user=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def log_feedback(
        self,
        task_id: str,
        from_agent: str,
        to_agent: str,
        content: str,
        feedback_type: str = 'question',
        user_id: Optional[int] = None
    ) -> TaskEvent:
        """
        记录反馈

        Args:
            task_id: 任务ID
            from_agent: 发送者Agent
            to_agent: 接收者Agent
            content: 反馈内容
            feedback_type: 反馈类型 (question, approval, rejection)
            user_id: 用户ID（人工反馈时）

        Returns:
            事件对象
        """
        event = TaskEvent(
            task_id=task_id,
            agent_name=from_agent,
            agent_type='human' if user_id else 'ai',
            event_type='feedback',
            content={
                'from': from_agent,
                'to': to_agent,
                'content': content,
                'type': feedback_type,
                'timestamp': datetime.utcnow().isoformat()
            },
            created_by_user=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def log_decision(
        self,
        task_id: str,
        decision_id: int,
        user_id: int,
        response: Dict[str, Any]
    ) -> TaskEvent:
        """
        记录决策

        Args:
            task_id: 任务ID
            decision_id: 决策ID
            user_id: 用户ID
            response: 决策结果

        Returns:
            事件对象
        """
        event = TaskEvent(
            task_id=task_id,
            agent_name='HumanAgent',
            agent_type='human',
            event_type='decision',
            content={
                'decision_id': decision_id,
                'response': response,
                'decided_at': datetime.utcnow().isoformat()
            },
            created_by_user=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def log_error(
        self,
        task_id: str,
        agent_name: str,
        error: str,
        user_id: Optional[int] = None
    ) -> TaskEvent:
        """
        记录错误

        Args:
            task_id: 任务ID
            agent_name: Agent名称
            error: 错误信息
            user_id: 用户ID

        Returns:
            事件对象
        """
        event = TaskEvent(
            task_id=task_id,
            agent_name=agent_name,
            agent_type='human' if user_id else 'ai',
            event_type='error',
            content={
                'error': error,
                'timestamp': datetime.utcnow().isoformat()
            },
            created_by_user=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def get_task_timeline(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务时间线

        Args:
            task_id: 任务ID

        Returns:
            时间线事件列表
        """
        events = self.db.query(TaskEvent).filter_by(
            task_id=task_id
        ).order_by(TaskEvent.created_at).all()

        timeline = []
        for event in events:
            timeline.append({
                'id': event.id,
                'agent_name': event.agent_name,
                'agent_type': event.agent_type,
                'event_type': event.event_type,
                'content': event.content,
                'created_at': event.created_at.isoformat(),
                'created_by_user': event.created_by_user
            })

        return timeline

    def get_agent_history(
        self,
        agent_name: str,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取Agent的操作历史

        Args:
            agent_name: Agent名称
            task_id: 任务ID（可选，限定到特定任务）
            limit: 返回数量限制

        Returns:
            操作历史列表
        """
        query = self.db.query(TaskEvent).filter_by(agent_name=agent_name)

        if task_id:
            query = query.filter_by(task_id=task_id)

        events = query.order_by(
            TaskEvent.created_at.desc()
        ).limit(limit).all()

        history = []
        for event in events:
            history.append({
                'id': event.id,
                'task_id': event.task_id,
                'event_type': event.event_type,
                'content': event.content,
                'created_at': event.created_at.isoformat()
            })

        return history

    def get_user_activity(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户的活动历史

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            活动历史列表
        """
        events = self.db.query(TaskEvent).filter_by(
            created_by_user=user_id
        ).order_by(
            TaskEvent.created_at.desc()
        ).limit(limit).all()

        activity = []
        for event in events:
            task = event.task
            activity.append({
                'id': event.id,
                'task_id': task.id,
                'task_title': task.title,
                'agent_name': event.agent_name,
                'event_type': event.event_type,
                'content': event.content,
                'created_at': event.created_at.isoformat()
            })

        return activity

    def get_statistics(
        self,
        task_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            task_id: 任务ID（可选）
            agent_name: Agent名称（可选）

        Returns:
            统计信息
        """
        query = self.db.query(TaskEvent)

        if task_id:
            query = query.filter_by(task_id=task_id)

        if agent_name:
            query = query.filter_by(agent_name=agent_name)

        total = query.count()
        ai_events = query.filter_by(agent_type='ai').count()
        human_events = query.filter_by(agent_type='human').count()

        event_types = {}
        for event_type in ['start', 'complete', 'artifact', 'feedback', 'decision', 'error']:
            count = query.filter_by(event_type=event_type).count()
            event_types[event_type] = count

        return {
            'total_events': total,
            'ai_events': ai_events,
            'human_events': human_events,
            'event_types': event_types
        }

    def search_events(
        self,
        task_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        event_type: Optional[str] = None,
        agent_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TaskEvent]:
        """
        搜索事件

        Args:
            task_id: 任务ID
            agent_name: Agent名称
            event_type: 事件类型
            agent_type: Agent类型
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            事件列表
        """
        query = self.db.query(TaskEvent)

        if task_id:
            query = query.filter_by(task_id=task_id)

        if agent_name:
            query = query.filter_by(agent_name=agent_name)

        if event_type:
            query = query.filter_by(event_type=event_type)

        if agent_type:
            query = query.filter_by(agent_type=agent_type)

        if start_date:
            query = query.filter(TaskEvent.created_at >= start_date)

        if end_date:
            query = query.filter(TaskEvent.created_at <= end_date)

        return query.order_by(TaskEvent.created_at.desc()).limit(limit).all()
