"""
IM群聊系统API路由

提供群组管理、消息发送、@提及、人工介入等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database.models import User
from .auth import get_current_active_user as get_current_user
from .dependencies import get_db
from ..im.group_manager import GroupManager, MemberRole
from ..im.message_router import MessageRouter, MessageType
from ..im.mention_handler import MentionHandler
from ..im.intervention_manager import InterventionManager, InterventionLevel

router = APIRouter(prefix="/api/im", tags=["IM"])


# ============================================================================
# Pydantic模型
# ============================================================================

class CreateProjectGroupRequest(BaseModel):
    """创建项目群组请求"""
    project_id: int
    name: Optional[str] = None
    description: Optional[str] = None


class CreateTaskThreadRequest(BaseModel):
    """创建任务线程请求"""
    task_id: int
    parent_group_id: Optional[int] = None


class AddMemberRequest(BaseModel):
    """添加成员请求"""
    user_id: int
    role: str = MemberRole.MEMBER


class UpdateMemberRoleRequest(BaseModel):
    """更新成员角色请求"""
    new_role: str


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    group_id: Optional[int] = None
    thread_id: Optional[int] = None
    content: str
    message_type: str = MessageType.TEXT
    extra_data: Optional[dict] = None
    reply_to: Optional[int] = None


class MarkAsReadRequest(BaseModel):
    """标记已读请求"""
    message_ids: List[int]


class RequestInterventionRequest(BaseModel):
    """请求人工介入"""
    task_id: int
    agent_name: str
    level: str
    reason: str
    context: Optional[dict] = None
    suggested_actions: Optional[List[str]] = None


class ProvideGuidanceRequest(BaseModel):
    """提供指导"""
    guidance: str
    actions: Optional[List[str]] = None


# ============================================================================
# 群组管理接口
# ============================================================================

@router.post("/groups/project")
def create_project_group(
    request: CreateProjectGroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建项目群组

    为什么: 为项目创建主群组用于团队沟通
    """
    manager = GroupManager(db)
    try:
        group = manager.create_project_group(
            project_id=request.project_id,
            creator_id=current_user.id,
            name=request.name,
            description=request.description
        )
        return {
            "id": group.id,
            "project_id": group.project_id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/threads/task")
def create_task_thread(
    request: CreateTaskThreadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建任务线程

    为什么: 为任务创建独立讨论线程
    """
    manager = GroupManager(db)
    try:
        thread = manager.create_task_thread(
            task_id=request.task_id,
            creator_id=current_user.id,
            parent_group_id=request.parent_group_id
        )
        return {
            "id": thread.id,
            "task_id": thread.task_id,
            "parent_group_id": thread.parent_group_id,
            "name": thread.name,
            "created_at": thread.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/groups/{group_id}/members")
def add_group_member(
    group_id: int,
    request: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    添加群组成员

    为什么: 动态添加成员到群组
    """
    manager = GroupManager(db)

    # 检查权限
    if not manager.check_permission(group_id, current_user.id, MemberRole.ADMIN):
        raise HTTPException(status_code=403, detail="Permission denied")

    member = manager.add_member(
        group_id=group_id,
        user_id=request.user_id,
        role=request.role,
        added_by=current_user.id
    )

    return {
        "group_id": member.group_id,
        "user_id": member.user_id,
        "role": member.role,
        "joined_at": member.joined_at.isoformat()
    }


@router.delete("/groups/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    移除群组成员

    为什么: 支持成员退出或被移除
    """
    manager = GroupManager(db)

    # 检查权限
    if not manager.check_permission(group_id, current_user.id, MemberRole.ADMIN):
        raise HTTPException(status_code=403, detail="Permission denied")

    success = manager.remove_member(group_id, user_id)
    return {"success": success}


@router.put("/groups/{group_id}/members/{user_id}/role")
def update_member_role(
    group_id: int,
    user_id: int,
    request: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新成员角色

    为什么: 权限管理
    """
    manager = GroupManager(db)

    # 检查权限
    if not manager.check_permission(group_id, current_user.id, MemberRole.ADMIN):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        member = manager.update_member_role(
            group_id=group_id,
            user_id=user_id,
            new_role=request.new_role
        )
        return {
            "group_id": member.group_id,
            "user_id": member.user_id,
            "role": member.role
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/groups/{group_id}/members")
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取群组成员列表

    为什么: 显示群组成员信息
    """
    manager = GroupManager(db)

    # 检查权限
    if not manager.check_permission(group_id, current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    members = manager.get_group_members(group_id)
    return {"members": members}


# ============================================================================
# 消息管理接口
# ============================================================================

@router.post("/messages")
def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息

    为什么: 统一的消息发送接口
    """
    router_obj = MessageRouter(db)

    try:
        message = router_obj.send_message(
            sender_id=current_user.id,
            group_id=request.group_id,
            thread_id=request.thread_id,
            content=request.content,
            message_type=request.message_type,
            extra_data=request.extra_data,
            reply_to=request.reply_to
        )

        # 处理@提及
        mention_handler = MentionHandler(db)
        mention_handler.process_mentions(
            message_id=message.id,
            content=request.content,
            sender_id=current_user.id
        )

        return {
            "id": message.id,
            "sender_id": message.sender_id,
            "group_id": message.group_id,
            "thread_id": message.thread_id,
            "content": message.content,
            "message_type": message.message_type,
            "sent_at": message.sent_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/messages")
def get_messages(
    group_id: Optional[int] = Query(None),
    thread_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    before: Optional[str] = Query(None),
    after: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取消息列表

    为什么: 支持消息历史查询和分页加载
    """
    router_obj = MessageRouter(db)

    # 解析时间参数
    before_dt = datetime.fromisoformat(before) if before else None
    after_dt = datetime.fromisoformat(after) if after else None

    messages = router_obj.get_messages(
        group_id=group_id,
        thread_id=thread_id,
        limit=limit,
        before=before_dt,
        after=after_dt
    )

    return {"messages": messages}


@router.post("/messages/read")
def mark_messages_as_read(
    request: MarkAsReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记消息为已读

    为什么: 跟踪用户阅读状态
    """
    router_obj = MessageRouter(db)
    count = router_obj.mark_as_read(
        user_id=current_user.id,
        message_ids=request.message_ids
    )
    return {"marked_count": count}


@router.get("/messages/unread/count")
def get_unread_count(
    group_id: Optional[int] = Query(None),
    thread_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取未读消息数

    为什么: 显示未读消息提示
    """
    router_obj = MessageRouter(db)
    count = router_obj.get_unread_count(
        user_id=current_user.id,
        group_id=group_id,
        thread_id=thread_id
    )
    return {"unread_count": count}


@router.get("/messages/search")
def search_messages(
    keyword: str = Query(...),
    group_id: Optional[int] = Query(None),
    thread_id: Optional[int] = Query(None),
    sender_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索消息

    为什么: 支持消息内容搜索
    """
    router_obj = MessageRouter(db)
    messages = router_obj.search_messages(
        keyword=keyword,
        group_id=group_id,
        thread_id=thread_id,
        sender_id=sender_id,
        limit=limit
    )
    return {"messages": messages}


# ============================================================================
# @提及接口
# ============================================================================

@router.get("/mentions")
def get_user_mentions(
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的@提及列表

    为什么: 显示用户被@的消息
    """
    handler = MentionHandler(db)
    mentions = handler.get_user_mentions(
        user_id=current_user.id,
        is_read=is_read,
        limit=limit
    )
    return {"mentions": mentions}


@router.post("/mentions/read")
def mark_mentions_as_read(
    request: MarkAsReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记@提及为已读

    为什么: 跟踪用户是否已查看@提及
    """
    handler = MentionHandler(db)
    count = handler.mark_mentions_as_read(
        user_id=current_user.id,
        mention_ids=request.message_ids
    )
    return {"marked_count": count}


@router.get("/mentions/unread/count")
def get_unread_mention_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取未读@提及数量

    为什么: 显示未读@提及数量徽章
    """
    handler = MentionHandler(db)
    count = handler.get_unread_mention_count(user_id=current_user.id)
    return {"unread_count": count}


# ============================================================================
# 人工介入接口
# ============================================================================

@router.post("/interventions")
def request_intervention(
    request: RequestInterventionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    请求人工介入

    为什么: Agent遇到问题时主动请求人工帮助
    """
    manager = InterventionManager(db)

    try:
        level = InterventionLevel(request.level)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention level")

    intervention = manager.request_intervention(
        task_id=request.task_id,
        agent_name=request.agent_name,
        level=level,
        reason=request.reason,
        context=request.context,
        suggested_actions=request.suggested_actions
    )

    return {
        "id": intervention.id,
        "task_id": intervention.task_id,
        "agent_name": intervention.agent_name,
        "level": intervention.level,
        "status": intervention.status,
        "requested_at": intervention.requested_at.isoformat()
    }


@router.put("/interventions/{request_id}/assign/{user_id}")
def assign_intervention(
    request_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分配介入请求

    为什么: 指定负责人处理介入请求
    """
    manager = InterventionManager(db)

    try:
        intervention = manager.assign_intervention(
            request_id=request_id,
            assignee_id=user_id
        )
        return {
            "id": intervention.id,
            "assigned_to": intervention.assigned_to,
            "status": intervention.status,
            "assigned_at": intervention.assigned_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/interventions/{request_id}/guidance")
def provide_guidance(
    request_id: int,
    request: ProvideGuidanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提供人工指导

    为什么: 人工给出解决方案或指导意见
    """
    manager = InterventionManager(db)

    try:
        intervention = manager.provide_guidance(
            request_id=request_id,
            user_id=current_user.id,
            guidance=request.guidance,
            actions=request.actions
        )
        return {
            "id": intervention.id,
            "status": intervention.status,
            "resolution": intervention.resolution,
            "resolved_at": intervention.resolved_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/interventions/{request_id}")
def cancel_intervention(
    request_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消介入请求

    为什么: Agent自行解决问题或请求不再需要
    """
    manager = InterventionManager(db)

    try:
        intervention = manager.cancel_intervention(
            request_id=request_id,
            reason=reason
        )
        return {
            "id": intervention.id,
            "status": intervention.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/interventions/pending")
def get_pending_interventions(
    level: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取待处理的介入请求

    为什么: 显示需要人工处理的请求列表
    """
    manager = InterventionManager(db)

    level_enum = None
    if level:
        try:
            level_enum = InterventionLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid intervention level")

    interventions = manager.get_pending_interventions(
        level=level_enum,
        limit=limit
    )

    return {"interventions": interventions}


@router.get("/interventions/stats")
def get_intervention_stats(
    task_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取介入统计信息

    为什么: 分析人工介入频率和模式
    """
    manager = InterventionManager(db)
    stats = manager.get_intervention_stats(task_id=task_id)
    return stats
