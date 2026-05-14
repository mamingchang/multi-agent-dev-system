"""
测试配置和工具

提供测试所需的fixtures、mock工具、测试数据生成器等。
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock
from datetime import datetime
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """创建真实的SQLite内存数据库用于测试"""
    from src.database.models import Base

    # 创建内存数据库
    engine = create_engine('sqlite:///:memory:', echo=False)

    # 创建所有表
    Base.metadata.create_all(engine)

    # 创建会话
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # 清理
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_with_data(test_db):
    """创建带有测试数据的真实数据库"""
    from src.database.models import Organization, User, Project

    # 创建测试组织
    org = Organization(
        name="Test Organization",
        slug="test-org",
        created_at=datetime.utcnow()
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)

    # 创建测试用户
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # 创建测试项目
    project = Project(
        name="Test Project",
        description="Test Description",
        organization_id=org.id,
        created_by=user.id,
        created_at=datetime.utcnow()
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)

    # 添加用户为项目成员
    from src.database.models import ProjectMember, UserRole
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=UserRole.OWNER
    )
    test_db.add(member)
    test_db.commit()

    # 返回数据库和测试数据
    yield {
        'db': test_db,
        'org': org,
        'user': user,
        'project': project
    }


@pytest.fixture
def mock_db_session():
    """Mock数据库会话"""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    return session


@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端"""
    client = Mock()

    def mock_generate(prompt: str, **kwargs) -> str:
        """模拟LLM生成"""
        return f"Mock response for: {prompt[:50]}..."

    client.generate = mock_generate
    return client


@pytest.fixture
def sample_user():
    """示例用户"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "developer",
        "organization_id": 1
    }


@pytest.fixture
def sample_organization():
    """示例组织"""
    return {
        "id": 1,
        "name": "Test Organization",
        "token_quota": 1000000,
        "token_used": 0,
        "max_concurrent_tasks": 3
    }


@pytest.fixture
def sample_project():
    """示例项目"""
    return {
        "id": 1,
        "name": "Test Project",
        "description": "A test project",
        "organization_id": 1,
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
    }


@pytest.fixture
def sample_task():
    """示例任务"""
    return {
        "id": 1,
        "title": "Implement user authentication",
        "description": "Add JWT-based authentication to the API",
        "project_id": 1,
        "status": "pending",
        "priority": 50,
        "workflow": ["ProductManager", "Architect", "Developer", "Tester"]
    }


# ============================================================================
# Mock工具
# ============================================================================

class MockLLMResponse:
    """Mock LLM响应"""

    def __init__(
        self,
        content: str,
        input_tokens: int = 100,
        output_tokens: int = 50,
        model: str = "claude-sonnet-4"
    ):
        self.content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model = model
        self.total_tokens = input_tokens + output_tokens


class MockLLMAdapter:
    """Mock LLM适配器"""

    def __init__(self, responses: List[str] = None):
        """
        初始化Mock适配器

        Args:
            responses: 预设的响应列表（按顺序返回）
        """
        self.responses = responses or []
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> MockLLMResponse:
        """
        生成响应

        Args:
            prompt: 提示词
            system_prompt: 系统提示词
            temperature: 温度
            max_tokens: 最大Token数

        Returns:
            MockLLMResponse: Mock响应
        """
        # 记录调用
        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timestamp": datetime.utcnow()
        })

        # 返回预设响应或默认响应
        if self.call_count < len(self.responses):
            content = self.responses[self.call_count]
        else:
            content = f"Mock response {self.call_count + 1}"

        self.call_count += 1

        return MockLLMResponse(
            content=content,
            input_tokens=len(prompt.split()),
            output_tokens=len(content.split())
        )


# ============================================================================
# 测试数据生成器
# ============================================================================

class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_email() -> str:
        """生成随机邮箱"""
        username = TestDataGenerator.random_string(8)
        domain = TestDataGenerator.random_string(6)
        return f"{username}@{domain}.com"

    @staticmethod
    def generate_user(
        username: str = None,
        email: str = None,
        role: str = "developer"
    ) -> Dict[str, Any]:
        """
        生成用户数据

        Args:
            username: 用户名
            email: 邮箱
            role: 角色

        Returns:
            dict: 用户数据
        """
        return {
            "id": random.randint(1, 10000),
            "username": username or TestDataGenerator.random_string(8),
            "email": email or TestDataGenerator.random_email(),
            "role": role,
            "organization_id": random.randint(1, 100),
            "created_at": datetime.utcnow()
        }

    @staticmethod
    def generate_organization(
        name: str = None,
        token_quota: int = 1000000
    ) -> Dict[str, Any]:
        """
        生成组织数据

        Args:
            name: 组织名称
            token_quota: Token配额

        Returns:
            dict: 组织数据
        """
        return {
            "id": random.randint(1, 10000),
            "name": name or f"Organization {TestDataGenerator.random_string(6)}",
            "token_quota": token_quota,
            "token_used": random.randint(0, token_quota // 2),
            "max_concurrent_tasks": random.randint(1, 10),
            "created_at": datetime.utcnow()
        }

    @staticmethod
    def generate_project(
        name: str = None,
        organization_id: int = 1
    ) -> Dict[str, Any]:
        """
        生成项目数据

        Args:
            name: 项目名称
            organization_id: 组织ID

        Returns:
            dict: 项目数据
        """
        tech_stacks = [
            ["Python", "FastAPI", "PostgreSQL"],
            ["JavaScript", "React", "Node.js"],
            ["Java", "Spring Boot", "MySQL"],
            ["Go", "Gin", "MongoDB"]
        ]

        return {
            "id": random.randint(1, 10000),
            "name": name or f"Project {TestDataGenerator.random_string(6)}",
            "description": f"Test project description {TestDataGenerator.random_string(20)}",
            "organization_id": organization_id,
            "tech_stack": random.choice(tech_stacks),
            "created_at": datetime.utcnow()
        }

    @staticmethod
    def generate_task(
        title: str = None,
        project_id: int = 1,
        status: str = "pending"
    ) -> Dict[str, Any]:
        """
        生成任务数据

        Args:
            title: 任务标题
            project_id: 项目ID
            status: 状态

        Returns:
            dict: 任务数据
        """
        workflows = [
            ["ProductManager", "Architect", "Developer", "Tester"],
            ["ProductManager", "Developer", "CodeReviewer"],
            ["Architect", "Developer", "Tester", "Deployer"]
        ]

        return {
            "id": random.randint(1, 10000),
            "title": title or f"Task {TestDataGenerator.random_string(10)}",
            "description": f"Test task description {TestDataGenerator.random_string(30)}",
            "project_id": project_id,
            "status": status,
            "priority": random.randint(0, 100),
            "workflow": random.choice(workflows),
            "created_at": datetime.utcnow()
        }


# ============================================================================
# 断言辅助函数
# ============================================================================

def assert_valid_response(response: Dict[str, Any], expected_keys: List[str]):
    """
    断言响应有效

    Args:
        response: 响应数据
        expected_keys: 期望的键列表
    """
    assert isinstance(response, dict), "响应应该是字典"

    for key in expected_keys:
        assert key in response, f"响应缺少键: {key}"


def assert_error_response(response: Dict[str, Any], expected_error: str = None):
    """
    断言错误响应

    Args:
        response: 响应数据
        expected_error: 期望的错误消息
    """
    assert "error" in response, "错误响应应该包含error字段"

    if expected_error:
        assert expected_error in response["error"], f"错误消息不匹配: {response['error']}"


def assert_token_usage(
    usage: Dict[str, int],
    min_tokens: int = 0,
    max_tokens: int = 100000
):
    """
    断言Token使用量

    Args:
        usage: Token使用量
        min_tokens: 最小Token数
        max_tokens: 最大Token数
    """
    assert "input_tokens" in usage, "缺少input_tokens"
    assert "output_tokens" in usage, "缺少output_tokens"
    assert "total_tokens" in usage, "缺少total_tokens"

    total = usage["total_tokens"]
    assert min_tokens <= total <= max_tokens, f"Token使用量超出范围: {total}"
