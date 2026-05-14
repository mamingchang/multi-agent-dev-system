"""
项目导入API路由

提供项目导入、分析、知识提取接口
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from .dependencies import get_db
from .auth import get_current_active_user as get_current_user
from ..database.models import User, UserRole, AuditAction
from ..database.database import Database, ProjectRepository
from ..database.organization_repository import OrganizationRepository, OrganizationMemberRepository
from ..project_import.git_importer import GitImporter
from ..project_import.code_analyzer import CodeAnalyzer
from ..project_import.knowledge_extractor import KnowledgeExtractor
from .audit_helper import log_audit

router = APIRouter(prefix="/api/import", tags=["Project Import"])


class ImportProjectRequest(BaseModel):
    """导入项目请求"""
    repo_url: str
    project_name: str
    organization_id: int  # 新增：必须指定组织
    branch: Optional[str] = None
    depth: Optional[int] = None
    description: Optional[str] = None  # 新增：项目描述


@router.post("/clone")
def clone_repository(
    request: ImportProjectRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    克隆Git仓库并创建项目

    改进：导入项目后自动创建数据库项目记录，与新建项目统一
    """
    with db.get_session() as session:
        # 1. 检查用户是否是组织成员
        member_repo = OrganizationMemberRepository(session)
        if not member_repo.is_member(request.organization_id, current_user.id):
            raise HTTPException(
                status_code=403,
                detail="您不是该组织的成员"
            )

        # 2. 检查组织项目数限制
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_id(request.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="组织不存在")

        if len(org.projects) >= org.max_projects:
            raise HTTPException(
                status_code=400,
                detail=f"组织项目数已达上限（{org.max_projects}）"
            )

        # 3. 克隆Git仓库到统一的代码目录
        from ..project_code import ProjectCodeManager
        code_manager = ProjectCodeManager()

        # 先创建项目记录以获取project_id
        project_repo = ProjectRepository(session)

        # 生成项目描述（如果没有提供）
        description = request.description
        if not description:
            description = f"从 {request.repo_url} 导入的项目"
            if request.branch:
                description += f"（分支: {request.branch}）"

        project = project_repo.create(
            name=request.project_name,
            description=description,
            created_by=current_user.id,
            organization_id=request.organization_id
        )

        # 4. 克隆代码到统一目录
        try:
            clone_result = code_manager.clone_repository(
                organization_id=request.organization_id,
                project_id=project.id,
                repo_url=request.repo_url,
                branch=request.branch,
                depth=request.depth or 1
            )

            # 更新项目的代码路径和Git信息
            project.code_path = clone_result["project_path"]
            project.repo_url = request.repo_url
            project.repo_branch = clone_result["branch"]
            project.project_type = "imported"
            session.commit()

        except Exception as e:
            # 克隆失败，删除项目记录
            session.delete(project)
            session.commit()
            raise HTTPException(status_code=400, detail=f"克隆仓库失败: {str(e)}")

        # 5. 添加创建者为Owner
        project_repo.add_member(
            project_id=project.id,
            user_id=current_user.id,
            role=UserRole.OWNER
        )

        # 6. 记录审计日志
        log_audit(
            session=session,
            action=AuditAction.PROJECT_CREATE,
            resource_type="project",
            resource_id=str(project.id),
            user=current_user,
            organization_id=request.organization_id,
            request=req,
            details={
                "name": project.name,
                "description": description,
                "organization_id": request.organization_id,
                "import_source": "git",
                "repo_url": request.repo_url,
                "branch": request.branch
            }
        )

        # 7. 返回完整信息
        return {
            "success": True,
            "project": {
                "id": project.id,
                "name": project.name,
                "description": description,
                "organization_id": request.organization_id,
                "created_by": current_user.id,
                "created_at": project.created_at.isoformat()
            },
            "git_info": {
                "project_path": clone_result["project_path"],
                "repo_url": clone_result["repo_url"],
                "branch": clone_result["branch"],
                "info": clone_result.get("info", {})
            }
        }


@router.post("/analyze/{project_id}")
def analyze_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    分析项目代码

    改进：使用统一的代码管理器
    """
    with db.get_session() as session:
        # 验证项目权限
        project_repo = ProjectRepository(session)
        project = project_repo.get_by_id(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查用户是否是项目成员
        if not project_repo.is_member(project_id, current_user.id):
            raise HTTPException(status_code=403, detail="您不是该项目的成员")

        # 检查项目代码是否存在
        if not project.code_path:
            raise HTTPException(
                status_code=404,
                detail="项目代码不存在"
            )

        # 分析项目
        analyzer = CodeAnalyzer()

        try:
            analysis = analyzer.analyze_project(project.code_path)
            return {
                "project_id": project_id,
                "project_name": project.name,
                "analysis": analysis
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/extract-knowledge/{project_id}")
def extract_knowledge(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    提取项目知识

    改进：使用统一的代码管理器
    """
    with db.get_session() as session:
        # 验证项目权限
        project_repo = ProjectRepository(session)
        project = project_repo.get_by_id(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查用户是否是项目成员
        if not project_repo.is_member(project_id, current_user.id):
            raise HTTPException(status_code=403, detail="您不是该项目的成员")

        # 检查项目代码是否存在
        if not project.code_path:
            raise HTTPException(
                status_code=404,
                detail="项目代码不存在"
            )

        # 提取知识
        extractor = KnowledgeExtractor()

        try:
            knowledge = extractor.extract_knowledge(project.code_path)
            summary = extractor.generate_summary(knowledge)

            return {
                "project_id": project_id,
                "project_name": project.name,
                "knowledge": knowledge,
                "summary": summary
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"提取知识失败: {str(e)}")


@router.post("/projects/{project_id}/pull")
def pull_updates(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    拉取项目更新

    改进：使用统一的代码管理器
    """
    with db.get_session() as session:
        # 验证项目权限
        project_repo = ProjectRepository(session)
        project = project_repo.get_by_id(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查用户是否是项目成员
        if not project_repo.is_member(project_id, current_user.id):
            raise HTTPException(status_code=403, detail="您不是该项目的成员")

        # 检查是否是Git项目
        if project.project_type != "imported":
            raise HTTPException(
                status_code=400,
                detail="只有导入的Git项目才能拉取更新"
            )

        # 拉取更新
        from ..project_code import ProjectCodeManager
        code_manager = ProjectCodeManager()

        try:
            result = code_manager.pull_updates(
                organization_id=project.organization_id,
                project_id=project.id
            )
            return {
                "project_id": project_id,
                "project_name": project.name,
                "result": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"拉取更新失败: {str(e)}")


@router.get("/projects/{project_name}/tree")
def get_file_tree(
    project_name: str,
    max_depth: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    获取项目文件树

    为什么: 查看项目结构
    """
    importer = GitImporter()

    # 获取项目路径
    projects = importer.list_projects()
    project = next((p for p in projects if p["name"] == project_name), None)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        tree = importer.get_file_tree(project["path"], max_depth)
        return tree
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
