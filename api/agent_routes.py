"""
Agent管理Web API

提供RESTful API来管理Agent的注册、更新、注销

端点：
- POST /api/agents: 注册新Agent
- GET /api/agents: 列出所有Agent
- GET /api/agents/{name}: 获取Agent详情
- PUT /api/agents/{name}: 更新Agent配置
- DELETE /api/agents/{name}: 注销Agent
- GET /api/agents/templates: 列出可用模板
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.agents.registration import AgentRegistration

router = APIRouter(prefix="/api/agents", tags=["agents"])

# 全局注册管理器实例
registration = AgentRegistration()


# ========== Pydantic模型 ==========

class AgentRegisterRequest(BaseModel):
    """Agent注册请求"""
    method: str = Field(..., description="注册方式：template/file/existing")
    name: str = Field(..., description="Agent名称")
    template: Optional[str] = Field(None, description="模板名称（method=template时使用）")
    source_agent: Optional[str] = Field(None, description="源Agent名称（method=existing时使用）")
    config: Optional[Dict[str, Any]] = Field(None, description="完整配置（method=file时使用）")
    overrides: Optional[Dict[str, Any]] = Field(None, description="覆盖配置项")


class AgentUpdateRequest(BaseModel):
    """Agent更新请求"""
    updates: Dict[str, Any] = Field(..., description="要更新的配置项")


class AgentResponse(BaseModel):
    """Agent响应"""
    name: str
    role: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    version: Optional[str] = None


class AgentDetailResponse(BaseModel):
    """Agent详细信息响应"""
    config: Dict[str, Any]


# ========== API端点 ==========

@router.post("", response_model=AgentDetailResponse, status_code=201)
async def register_agent(request: AgentRegisterRequest):
    """
    注册新Agent

    支持三种注册方式：
    1. template: 从模板创建
    2. file: 从完整配置创建
    3. existing: 从已有Agent复制

    示例：
    ```json
    {
        "method": "template",
        "name": "pm1",
        "template": "product_manager",
        "overrides": {
            "description": "我的产品经理Agent"
        }
    }
    ```
    """
    try:
        if request.method == "template":
            if not request.template:
                raise HTTPException(status_code=400, detail="template参数是必需的")

            config = registration.register_from_template(
                request.name,
                request.template,
                request.overrides
            )

        elif request.method == "file":
            if not request.config:
                raise HTTPException(status_code=400, detail="config参数是必需的")

            # 将config保存为临时文件，然后导入
            import tempfile
            import yaml

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(request.config, f, allow_unicode=True)
                temp_path = Path(f.name)

            try:
                config = registration.register_from_file(temp_path)
            finally:
                temp_path.unlink()

        elif request.method == "existing":
            if not request.source_agent:
                raise HTTPException(status_code=400, detail="source_agent参数是必需的")

            config = registration.register_from_existing(
                request.source_agent,
                request.name,
                request.overrides
            )

        else:
            raise HTTPException(status_code=400, detail=f"不支持的注册方式: {request.method}")

        return AgentDetailResponse(config=config)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """
    列出所有已注册的Agent

    返回Agent列表，包含基本信息
    """
    try:
        agents = registration.list_agents()
        return [AgentResponse(**agent) for agent in agents]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出Agent失败: {str(e)}")


@router.get("/{agent_name}", response_model=AgentDetailResponse)
async def get_agent(agent_name: str):
    """
    获取Agent详细配置

    返回完整的Agent配置字典
    """
    try:
        config = registration.load_config(agent_name)
        return AgentDetailResponse(config=config)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent配置失败: {str(e)}")


@router.put("/{agent_name}", response_model=AgentDetailResponse)
async def update_agent(agent_name: str, request: AgentUpdateRequest):
    """
    更新Agent配置

    支持部分更新，只需提供要修改的字段

    示例：
    ```json
    {
        "updates": {
            "description": "新的描述",
            "llm": {
                "temperature": 0.8
            }
        }
    }
    ```
    """
    try:
        config = registration.update_config(agent_name, request.updates)
        return AgentDetailResponse(config=config)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Agent失败: {str(e)}")


@router.delete("/{agent_name}", status_code=204)
async def unregister_agent(agent_name: str, backup: bool = True):
    """
    注销Agent

    参数：
    - backup: 是否备份配置文件（默认True）
    """
    try:
        registration.unregister(agent_name, backup=backup)
        return None

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注销Agent失败: {str(e)}")


@router.get("/templates/list", response_model=List[str])
async def list_templates():
    """
    列出可用的Agent模板

    返回模板名称列表
    """
    try:
        template_dir = Path.cwd() / 'config' / 'templates'

        if not template_dir.exists():
            return []

        templates = [f.stem for f in template_dir.glob('*.yaml')]
        return templates

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出模板失败: {str(e)}")


@router.get("/templates/{template_name}", response_model=AgentDetailResponse)
async def get_template(template_name: str):
    """
    获取模板详细配置

    返回模板的完整配置
    """
    try:
        template_path = Path.cwd() / 'config' / 'templates' / f"{template_name}.yaml"

        if not template_path.exists():
            raise HTTPException(status_code=404, detail=f"模板 '{template_name}' 不存在")

        import yaml
        with open(template_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return AgentDetailResponse(config=config)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")
