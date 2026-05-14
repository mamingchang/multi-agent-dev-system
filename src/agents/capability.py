"""
Agent能力声明

定义Agent的能力、依赖、配置等元信息。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentScope(str, Enum):
    """Agent作用域"""
    GLOBAL = "global"  # 全局可用
    ORGANIZATION = "organization"  # 组织内可用
    PROJECT = "project"  # 项目内可用


@dataclass
class AgentCapability:
    """Agent能力声明"""

    # 基本信息
    name: str  # Agent名称（唯一标识）
    display_name: str  # 显示名称
    description: str  # 描述
    version: str  # 版本号
    author: str  # 作者

    # 能力范围
    task_types: List[str] = field(default_factory=list)  # 能处理的任务类型
    tech_stacks: List[str] = field(default_factory=list)  # 支持的技术栈
    domains: List[str] = field(default_factory=list)  # 擅长的领域

    # 依赖关系
    required_inputs: List[str] = field(default_factory=list)  # 需要的输入产物类型
    output_artifacts: List[str] = field(default_factory=list)  # 产生的产物类型
    depends_on: List[str] = field(default_factory=list)  # 依赖的其他Agent

    # 配置参数
    config_schema: Dict[str, Any] = field(default_factory=dict)  # 配置参数schema
    default_config: Dict[str, Any] = field(default_factory=dict)  # 默认配置

    # 作用域和权限
    scope: AgentScope = AgentScope.GLOBAL  # 作用域
    scope_id: Optional[int] = None  # 作用域ID（组织ID或项目ID）

    # 元数据
    tags: List[str] = field(default_factory=list)  # 标签
    icon: Optional[str] = None  # 图标URL
    documentation_url: Optional[str] = None  # 文档URL

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "task_types": self.task_types,
            "tech_stacks": self.tech_stacks,
            "domains": self.domains,
            "required_inputs": self.required_inputs,
            "output_artifacts": self.output_artifacts,
            "depends_on": self.depends_on,
            "config_schema": self.config_schema,
            "default_config": self.default_config,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "tags": self.tags,
            "icon": self.icon,
            "documentation_url": self.documentation_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCapability":
        """从字典创建"""
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            version=data["version"],
            author=data["author"],
            task_types=data.get("task_types", []),
            tech_stacks=data.get("tech_stacks", []),
            domains=data.get("domains", []),
            required_inputs=data.get("required_inputs", []),
            output_artifacts=data.get("output_artifacts", []),
            depends_on=data.get("depends_on", []),
            config_schema=data.get("config_schema", {}),
            default_config=data.get("default_config", {}),
            scope=AgentScope(data.get("scope", "global")),
            scope_id=data.get("scope_id"),
            tags=data.get("tags", []),
            icon=data.get("icon"),
            documentation_url=data.get("documentation_url")
        )


# ============================================================================
# 内置Agent能力声明
# ============================================================================

BUILTIN_AGENTS = [
    AgentCapability(
        name="ProductManager",
        display_name="产品经理",
        description="负责需求分析和PRD编写",
        version="1.0.0",
        author="System",
        task_types=["feature", "enhancement", "requirement"],
        tech_stacks=["*"],  # 支持所有技术栈
        domains=["product", "requirement", "analysis"],
        required_inputs=[],
        output_artifacts=["prd", "requirement_doc"],
        depends_on=[],
        default_config={
            "model": "claude-sonnet-4",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        tags=["builtin", "requirement"]
    ),

    AgentCapability(
        name="Architect",
        display_name="架构师",
        description="负责系统架构设计",
        version="1.0.0",
        author="System",
        task_types=["feature", "enhancement", "refactor"],
        tech_stacks=["*"],
        domains=["architecture", "design", "system"],
        required_inputs=["prd", "requirement_doc"],
        output_artifacts=["architecture_doc", "design_doc"],
        depends_on=["ProductManager"],
        default_config={
            "model": "claude-opus-4",
            "temperature": 0.5,
            "max_tokens": 6000
        },
        tags=["builtin", "design"]
    ),

    AgentCapability(
        name="Developer",
        display_name="开发工程师",
        description="负责代码实现",
        version="1.0.0",
        author="System",
        task_types=["feature", "enhancement", "bugfix", "refactor"],
        tech_stacks=["Python", "JavaScript", "Java", "Go", "Rust"],
        domains=["coding", "implementation"],
        required_inputs=["architecture_doc", "design_doc"],
        output_artifacts=["code", "implementation"],
        depends_on=["Architect"],
        default_config={
            "model": "claude-sonnet-4",
            "temperature": 0.3,
            "max_tokens": 8000
        },
        tags=["builtin", "coding"]
    ),

    AgentCapability(
        name="CodeReviewer",
        display_name="代码审查员",
        description="负责代码审查和质量把控",
        version="1.0.0",
        author="System",
        task_types=["feature", "enhancement", "bugfix", "refactor"],
        tech_stacks=["*"],
        domains=["code_review", "quality"],
        required_inputs=["code", "implementation"],
        output_artifacts=["review_report", "feedback"],
        depends_on=["Developer"],
        default_config={
            "model": "claude-opus-4",
            "temperature": 0.2,
            "max_tokens": 4000
        },
        tags=["builtin", "review"]
    ),

    AgentCapability(
        name="Tester",
        display_name="测试工程师",
        description="负责测试用例编写和执行",
        version="1.0.0",
        author="System",
        task_types=["feature", "enhancement", "bugfix"],
        tech_stacks=["*"],
        domains=["testing", "qa"],
        required_inputs=["code", "implementation"],
        output_artifacts=["test_cases", "test_report"],
        depends_on=["Developer"],
        default_config={
            "model": "claude-sonnet-4",
            "temperature": 0.4,
            "max_tokens": 5000
        },
        tags=["builtin", "testing"]
    ),

    AgentCapability(
        name="Deployer",
        display_name="部署工程师",
        description="负责部署和运维",
        version="1.0.0",
        author="System",
        task_types=["deployment", "release"],
        tech_stacks=["Docker", "Kubernetes", "AWS", "Azure", "GCP"],
        domains=["deployment", "devops"],
        required_inputs=["code", "test_report"],
        output_artifacts=["deployment_config", "deployment_report"],
        depends_on=["Tester"],
        default_config={
            "model": "claude-sonnet-4",
            "temperature": 0.2,
            "max_tokens": 3000
        },
        tags=["builtin", "deployment"]
    ),

    AgentCapability(
        name="DocumentWriter",
        display_name="文档编写员",
        description="负责技术文档编写",
        version="1.0.0",
        author="System",
        task_types=["documentation"],
        tech_stacks=["*"],
        domains=["documentation", "writing"],
        required_inputs=["code", "architecture_doc"],
        output_artifacts=["documentation", "user_guide"],
        depends_on=["Developer"],
        default_config={
            "model": "claude-sonnet-4",
            "temperature": 0.6,
            "max_tokens": 6000
        },
        tags=["builtin", "documentation"]
    )
]
