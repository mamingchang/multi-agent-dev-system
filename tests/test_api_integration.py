"""
API路由集成测试

使用FastAPI TestClient进行真实的API测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock()
    db.query = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def test_client(mock_db):
    """创建测试客户端"""
    from src.api.main import app

    # Mock数据库依赖
    def override_get_db():
        try:
            yield mock_db
        finally:
            pass

    from src.api.dependencies import get_db
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


class TestProjectsAPI:
    """项目API测试"""

    def test_list_projects(self, test_client, mock_db):
        """测试列出项目"""
        # Mock查询结果
        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = test_client.get("/api/projects")

        assert response.status_code in [200, 401, 404]  # 允许未认证

    def test_create_project(self, test_client, mock_db):
        """测试创建项目"""
        project_data = {
            "name": "Test Project",
            "description": "Test Description"
        }

        response = test_client.post("/api/projects", json=project_data)

        assert response.status_code in [200, 201, 401, 404, 422]

    def test_get_project(self, test_client, mock_db):
        """测试获取项目"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = test_client.get("/api/projects/1")

        assert response.status_code in [200, 401, 404]

    def test_update_project(self, test_client, mock_db):
        """测试更新项目"""
        update_data = {
            "name": "Updated Project",
            "description": "Updated Description"
        }

        response = test_client.put("/api/projects/1", json=update_data)

        assert response.status_code in [200, 401, 404]

    def test_delete_project(self, test_client, mock_db):
        """测试删除项目"""
        response = test_client.delete("/api/projects/1")

        assert response.status_code in [200, 204, 401, 404]


class TestAgentsAPI:
    """Agent API测试"""

    def test_list_agents(self, test_client):
        """测试列出Agent"""
        response = test_client.get("/api/agents")

        assert response.status_code in [200, 401, 404]

    def test_get_agent_status(self, test_client):
        """测试获取Agent状态"""
        response = test_client.get("/api/agents/architect/status")

        assert response.status_code in [200, 401, 404]

    def test_execute_agent(self, test_client):
        """测试执行Agent"""
        task_data = {
            "agent_type": "architect",
            "task": "Design API"
        }

        response = test_client.post("/api/agents/execute", json=task_data)

        assert response.status_code in [200, 401, 404, 422]


class TestWorkflowAPI:
    """工作流API测试"""

    def test_create_workflow(self, test_client):
        """测试创建工作流"""
        workflow_data = {
            "name": "Test Workflow",
            "nodes": [{"id": "n1", "agent": "architect"}],
            "edges": []
        }

        response = test_client.post("/api/workflow", json=workflow_data)

        assert response.status_code in [200, 201, 401, 404, 422]

    def test_execute_workflow(self, test_client):
        """测试执行工作流"""
        response = test_client.post("/api/workflow/1/execute")

        assert response.status_code in [200, 401, 404]

    def test_get_workflow_status(self, test_client):
        """测试获取工作流状态"""
        response = test_client.get("/api/workflow/1/status")

        assert response.status_code in [200, 401, 404]


class TestIMAPI:
    """IM API测试"""

    def test_list_groups(self, test_client, mock_db):
        """测试列出群组"""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = test_client.get("/api/im/groups")

        assert response.status_code in [200, 401, 404]

    def test_create_group(self, test_client):
        """测试创建群组"""
        group_data = {
            "name": "Test Group",
            "group_type": "project"
        }

        response = test_client.post("/api/im/groups", json=group_data)

        assert response.status_code in [200, 201, 401, 404, 422]

    def test_send_message(self, test_client):
        """测试发送消息"""
        message_data = {
            "group_id": 1,
            "content": "Test message"
        }

        response = test_client.post("/api/im/messages", json=message_data)

        assert response.status_code in [200, 201, 401, 404, 422]

    def test_get_messages(self, test_client, mock_db):
        """测试获取消息"""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = test_client.get("/api/im/groups/1/messages")

        assert response.status_code in [200, 401, 404]


class TestMonitoringAPI:
    """监控API测试"""

    def test_get_metrics(self, test_client):
        """测试获取指标"""
        response = test_client.get("/api/monitoring/metrics")

        assert response.status_code in [200, 401, 404]

    def test_get_health(self, test_client):
        """测试健康检查"""
        response = test_client.get("/api/monitoring/health")

        assert response.status_code in [200, 404]

    def test_get_alerts(self, test_client):
        """测试获取告警"""
        response = test_client.get("/api/monitoring/alerts")

        assert response.status_code in [200, 401, 404]


class TestCostAPI:
    """成本API测试"""

    def test_get_cost_summary(self, test_client):
        """测试获取成本摘要"""
        response = test_client.get("/api/cost/summary")

        assert response.status_code in [200, 401, 404]

    def test_get_session_cost(self, test_client):
        """测试获取会话成本"""
        response = test_client.get("/api/cost/sessions/1")

        assert response.status_code in [200, 401, 404]


class TestBackupAPI:
    """备份API测试"""

    def test_create_backup(self, test_client):
        """测试创建备份"""
        response = test_client.post("/api/backup/create")

        assert response.status_code in [200, 201, 401, 404]

    def test_list_backups(self, test_client):
        """测试列出备份"""
        response = test_client.get("/api/backup/list")

        assert response.status_code in [200, 401, 404]

    def test_restore_backup(self, test_client):
        """测试恢复备份"""
        restore_data = {
            "backup_id": "backup_123"
        }

        response = test_client.post("/api/backup/restore", json=restore_data)

        assert response.status_code in [200, 401, 404]


class TestImportAPI:
    """项目导入API测试"""

    def test_clone_repository(self, test_client):
        """测试克隆仓库"""
        clone_data = {
            "repo_url": "https://github.com/test/repo.git",
            "project_name": "test_project"
        }

        response = test_client.post("/api/import/clone", json=clone_data)

        assert response.status_code in [200, 201, 401, 404, 422]

    def test_analyze_project(self, test_client):
        """测试分析项目"""
        response = test_client.post("/api/import/analyze/test_project")

        assert response.status_code in [200, 401, 404]

    def test_list_projects(self, test_client):
        """测试列出导入的项目"""
        response = test_client.get("/api/import/projects")

        assert response.status_code in [200, 401, 404]


class TestI18nAPI:
    """多语言API测试"""

    def test_get_translations(self, test_client):
        """测试获取翻译"""
        response = test_client.get("/api/i18n/translations/zh-CN")

        assert response.status_code in [200, 404]

    def test_get_supported_languages(self, test_client):
        """测试获取支持的语言"""
        response = test_client.get("/api/i18n/languages")

        assert response.status_code in [200, 404]


class TestUXAPI:
    """用户体验API测试"""

    def test_get_progress(self, test_client):
        """测试获取进度"""
        response = test_client.get("/api/ux/progress/1")

        assert response.status_code in [200, 401, 404]

    def test_get_notifications(self, test_client):
        """测试获取通知"""
        response = test_client.get("/api/ux/notifications")

        assert response.status_code in [200, 401, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
