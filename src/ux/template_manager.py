"""
任务模板系统

提供预定义的任务模板，加速任务创建。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TemplateScope(str, Enum):
    """模板作用域"""
    PUBLIC = "public"  # 公开模板
    ORGANIZATION = "organization"  # 组织模板
    USER = "user"  # 用户私有模板


class TemplateCategory(str, Enum):
    """模板分类"""
    FEATURE = "feature"  # 功能开发
    BUGFIX = "bugfix"  # Bug修复
    REFACTOR = "refactor"  # 重构
    OPTIMIZATION = "optimization"  # 优化
    DEPLOYMENT = "deployment"  # 部署
    DOCUMENTATION = "documentation"  # 文档


@dataclass
class TaskTemplate:
    """任务模板"""

    # 基本信息
    id: str  # 模板ID
    name: str  # 模板名称
    description: str  # 模板描述
    category: TemplateCategory  # 分类

    # 模板内容
    title_template: str  # 标题模板
    description_template: str  # 描述模板
    workflow: List[str]  # 推荐工作流

    # 配置
    tech_stacks: List[str] = field(default_factory=list)  # 适用技术栈
    estimated_hours: Optional[int] = None  # 预估工时
    priority: int = 50  # 默认优先级

    # 参数
    parameters: Dict[str, Any] = field(default_factory=dict)  # 模板参数

    # 作用域
    scope: TemplateScope = TemplateScope.PUBLIC
    scope_id: Optional[int] = None  # 组织ID或用户ID

    # 元数据
    author: str = ""
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "title_template": self.title_template,
            "description_template": self.description_template,
            "workflow": self.workflow,
            "tech_stacks": self.tech_stacks,
            "estimated_hours": self.estimated_hours,
            "priority": self.priority,
            "parameters": self.parameters,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "author": self.author,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def render(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染模板

        Args:
            params: 参数字典

        Returns:
            dict: 渲染后的任务数据
        """
        # 替换标题中的参数
        title = self.title_template
        for key, value in params.items():
            title = title.replace(f"{{{key}}}", str(value))

        # 替换描述中的参数
        description = self.description_template
        for key, value in params.items():
            description = description.replace(f"{{{key}}}", str(value))

        return {
            "title": title,
            "description": description,
            "workflow": self.workflow.copy(),
            "priority": self.priority,
            "estimated_hours": self.estimated_hours
        }


# ============================================================================
# 预定义模板
# ============================================================================

BUILTIN_TEMPLATES = [
    TaskTemplate(
        id="login_register",
        name="用户登录注册",
        description="实现用户登录和注册功能",
        category=TemplateCategory.FEATURE,
        title_template="实现{auth_method}用户登录注册",
        description_template="""实现用户登录和注册功能：

认证方式：{auth_method}
技术栈：{tech_stack}

功能需求：
1. 用户注册（邮箱/手机号）
2. 用户登录
3. 密码加密存储
4. Token生成和验证
5. 登录状态管理

安全要求：
- 密码强度验证
- 防暴力破解
- Token过期机制
""",
        workflow=["ProductManager", "Architect", "Developer", "CodeReviewer", "Tester"],
        tech_stacks=["Python", "JavaScript", "Java"],
        estimated_hours=16,
        priority=80,
        parameters={
            "auth_method": "JWT",
            "tech_stack": "FastAPI + PostgreSQL"
        },
        tags=["authentication", "security", "common"]
    ),

    TaskTemplate(
        id="crud_api",
        name="CRUD API开发",
        description="实现标准的增删改查API",
        category=TemplateCategory.FEATURE,
        title_template="实现{resource}的CRUD API",
        description_template="""实现{resource}的CRUD API：

资源：{resource}
技术栈：{tech_stack}

API端点：
- POST /{resource} - 创建
- GET /{resource} - 列表查询
- GET /{resource}/{{id}} - 详情查询
- PUT /{resource}/{{id}} - 更新
- DELETE /{resource}/{{id}} - 删除

功能要求：
1. 参数验证
2. 分页支持
3. 排序和过滤
4. 错误处理
5. API文档
""",
        workflow=["ProductManager", "Developer", "CodeReviewer", "Tester"],
        tech_stacks=["Python", "JavaScript", "Java", "Go"],
        estimated_hours=8,
        priority=60,
        parameters={
            "resource": "users",
            "tech_stack": "FastAPI + SQLAlchemy"
        },
        tags=["api", "crud", "common"]
    ),

    TaskTemplate(
        id="bug_fix",
        name="Bug修复",
        description="修复已知Bug",
        category=TemplateCategory.BUGFIX,
        title_template="修复：{bug_description}",
        description_template="""Bug描述：
{bug_description}

复现步骤：
{reproduce_steps}

期望行为：
{expected_behavior}

实际行为：
{actual_behavior}

影响范围：
{impact}

优先级：{priority}
""",
        workflow=["Developer", "CodeReviewer", "Tester"],
        tech_stacks=["*"],
        estimated_hours=4,
        priority=90,
        parameters={
            "bug_description": "描述Bug",
            "reproduce_steps": "1. ...\n2. ...",
            "expected_behavior": "期望的行为",
            "actual_behavior": "实际的行为",
            "impact": "影响范围",
            "priority": "高"
        },
        tags=["bugfix", "maintenance"]
    ),

    TaskTemplate(
        id="performance_optimization",
        name="性能优化",
        description="优化系统性能",
        category=TemplateCategory.OPTIMIZATION,
        title_template="优化{component}性能",
        description_template="""性能优化任务：

目标组件：{component}
当前性能：{current_performance}
目标性能：{target_performance}

优化方向：
1. {optimization_1}
2. {optimization_2}
3. {optimization_3}

验证方法：
- 性能测试
- 压力测试
- 监控指标对比
""",
        workflow=["Architect", "Developer", "Tester"],
        tech_stacks=["*"],
        estimated_hours=12,
        priority=70,
        parameters={
            "component": "API接口",
            "current_performance": "响应时间500ms",
            "target_performance": "响应时间<200ms",
            "optimization_1": "数据库查询优化",
            "optimization_2": "缓存策略",
            "optimization_3": "代码优化"
        },
        tags=["optimization", "performance"]
    ),

    TaskTemplate(
        id="refactor_code",
        name="代码重构",
        description="重构现有代码",
        category=TemplateCategory.REFACTOR,
        title_template="重构{module}模块",
        description_template="""重构任务：

目标模块：{module}
重构原因：{reason}

重构目标：
1. {goal_1}
2. {goal_2}
3. {goal_3}

重构范围：
{scope}

注意事项：
- 保持功能不变
- 添加单元测试
- 更新文档
""",
        workflow=["Architect", "Developer", "CodeReviewer", "Tester"],
        tech_stacks=["*"],
        estimated_hours=16,
        priority=50,
        parameters={
            "module": "认证模块",
            "reason": "代码复杂度高，难以维护",
            "goal_1": "降低代码复杂度",
            "goal_2": "提高可测试性",
            "goal_3": "改善代码可读性",
            "scope": "src/auth/"
        },
        tags=["refactor", "maintenance"]
    ),

    TaskTemplate(
        id="deployment",
        name="部署上线",
        description="部署应用到生产环境",
        category=TemplateCategory.DEPLOYMENT,
        title_template="部署{version}到{environment}",
        description_template="""部署任务：

版本：{version}
环境：{environment}
部署时间：{deploy_time}

部署内容：
{changes}

部署步骤：
1. 备份当前版本
2. 停止服务
3. 更新代码
4. 数据库迁移
5. 启动服务
6. 验证功能
7. 监控观察

回滚方案：
{rollback_plan}
""",
        workflow=["Deployer"],
        tech_stacks=["Docker", "Kubernetes"],
        estimated_hours=4,
        priority=100,
        parameters={
            "version": "v1.2.0",
            "environment": "生产环境",
            "deploy_time": "2026-05-10 02:00",
            "changes": "- 新增功能A\n- 修复Bug B",
            "rollback_plan": "回滚到v1.1.0"
        },
        tags=["deployment", "release"]
    ),

    TaskTemplate(
        id="api_documentation",
        name="API文档编写",
        description="编写API接口文档",
        category=TemplateCategory.DOCUMENTATION,
        title_template="编写{api_name} API文档",
        description_template="""API文档编写：

API名称：{api_name}
API版本：{api_version}

文档内容：
1. API概述
2. 认证方式
3. 端点列表
4. 请求/响应示例
5. 错误码说明
6. 使用示例

文档格式：{doc_format}
""",
        workflow=["DocumentWriter"],
        tech_stacks=["*"],
        estimated_hours=6,
        priority=40,
        parameters={
            "api_name": "用户管理",
            "api_version": "v1.0",
            "doc_format": "OpenAPI 3.0"
        },
        tags=["documentation", "api"]
    )
]


class TemplateManager:
    """模板管理器"""

    def __init__(self):
        """初始化管理器"""
        self.templates: Dict[str, TaskTemplate] = {}

        # 加载内置模板
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """加载内置模板"""
        for template in BUILTIN_TEMPLATES:
            self.templates[template.id] = template

    def add_template(self, template: TaskTemplate) -> bool:
        """
        添加模板

        Args:
            template: 任务模板

        Returns:
            bool: 是否添加成功
        """
        if template.id in self.templates:
            return False

        template.created_at = datetime.utcnow()
        template.updated_at = datetime.utcnow()
        self.templates[template.id] = template
        return True

    def update_template(self, template: TaskTemplate) -> bool:
        """
        更新模板

        Args:
            template: 任务模板

        Returns:
            bool: 是否更新成功
        """
        if template.id not in self.templates:
            return False

        template.updated_at = datetime.utcnow()
        self.templates[template.id] = template
        return True

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            bool: 是否删除成功
        """
        if template_id not in self.templates:
            return False

        del self.templates[template_id]
        return True

    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """
        获取模板

        Args:
            template_id: 模板ID

        Returns:
            Optional[TaskTemplate]: 模板
        """
        return self.templates.get(template_id)

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        scope: Optional[TemplateScope] = None,
        scope_id: Optional[int] = None,
        tech_stack: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[TaskTemplate]:
        """
        列出模板

        Args:
            category: 分类过滤
            scope: 作用域过滤
            scope_id: 作用域ID过滤
            tech_stack: 技术栈过滤
            tags: 标签过滤

        Returns:
            List[TaskTemplate]: 模板列表
        """
        results = list(self.templates.values())

        # 分类过滤
        if category:
            results = [t for t in results if t.category == category]

        # 作用域过滤
        if scope:
            results = [t for t in results if t.scope == scope]

        if scope_id is not None:
            results = [t for t in results if t.scope_id == scope_id]

        # 技术栈过滤
        if tech_stack:
            results = [
                t for t in results
                if "*" in t.tech_stacks or tech_stack in t.tech_stacks
            ]

        # 标签过滤
        if tags:
            results = [
                t for t in results
                if any(tag in t.tags for tag in tags)
            ]

        # 按使用次数排序
        results.sort(key=lambda t: t.usage_count, reverse=True)

        return results

    def use_template(self, template_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用模板

        Args:
            template_id: 模板ID
            params: 参数

        Returns:
            dict: 渲染后的任务数据
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        # 增加使用次数
        template.usage_count += 1

        # 渲染模板
        return template.render(params)


# 全局模板管理器实例
template_manager = TemplateManager()
