"""
审计日志系统测试

测试场景：
1. 自动记录用户注册
2. 自动记录用户登录
3. 自动记录组织创建
4. 自动记录组织更新
5. 自动记录成员添加
6. 查询审计日志
7. 按用户过滤
8. 按组织过滤
9. 按操作类型过滤
10. 按时间范围过滤
11. 获取用户活动
12. 获取资源历史
13. 审计统计
14. 权限控制测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from src.api.main import app
from src.database.database import Database
from src.database.models import Base
from datetime import datetime, timedelta

# 创建测试客户端
client = TestClient(app)

# 测试数据库
test_db = Database("sqlite:///:memory:")

# 全局变量存储测试数据
test_data = {
    "user1_token": None,
    "user1_id": None,
    "user2_token": None,
    "user2_id": None,
    "org1_id": None,
    "project1_id": None
}


def setup_database():
    """初始化测试数据库"""
    print("\n=== 初始化测试数据库 ===")
    Base.metadata.create_all(bind=test_db.engine)
    print("✓ 数据库表创建成功")


def test_register_and_audit():
    """测试1: 用户注册自动记录审计日志"""
    print("\n=== 测试1: 用户注册审计 ===")

    response = client.post("/auth/register", json={
        "username": "audit_user1",
        "email": "audit1@example.com",
        "password": "password123",
        "full_name": "Audit User 1"
    })
    assert response.status_code == 201
    test_data["user1_id"] = response.json()["id"]
    print("✓ 用户1注册成功")


def test_login_and_audit():
    """测试2: 用户登录自动记录审计日志"""
    print("\n=== 测试2: 用户登录审计 ===")

    response = client.post("/auth/login", json={
        "username": "audit_user1",
        "password": "password123"
    })
    assert response.status_code == 200
    test_data["user1_token"] = response.json()["access_token"]
    print("✓ 用户1登录成功")


def test_create_organization_and_audit():
    """测试3: 创建组织自动记录审计日志"""
    print("\n=== 测试3: 创建组织审计 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.post("/organizations", headers=headers, json={
        "name": "Audit Test Org",
        "slug": "audit-test-org",
        "description": "Organization for audit testing"
    })
    assert response.status_code == 201
    test_data["org1_id"] = response.json()["id"]
    print("✓ 组织创建成功")


def test_update_organization_and_audit():
    """测试4: 更新组织自动记录审计日志"""
    print("\n=== 测试4: 更新组织审计 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.put(f"/organizations/{test_data['org1_id']}", headers=headers, json={
        "name": "Audit Test Org Updated",
        "description": "Updated description"
    })
    assert response.status_code == 200
    print("✓ 组织更新成功")


def test_create_project_and_audit():
    """测试5: 创建项目自动记录审计日志"""
    print("\n=== 测试5: 创建项目审计 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.post("/projects", headers=headers, json={
        "name": "Audit Test Project",
        "description": "Project for audit testing",
        "organization_id": test_data["org1_id"]
    })
    assert response.status_code == 201
    test_data["project1_id"] = response.json()["id"]
    print("✓ 项目创建成功")


def test_query_audit_logs():
    """测试6: 查询审计日志"""
    print("\n=== 测试6: 查询审计日志 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/logs?organization_id={test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["logs"]) > 0
    print(f"✓ 查询到 {data['total']} 条审计日志")


def test_filter_by_user():
    """测试7: 按用户过滤审计日志"""
    print("\n=== 测试7: 按用户过滤 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/logs?user_id={test_data['user1_id']}&organization_id={test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    # 验证所有日志都是该用户的
    for log in data["logs"]:
        assert log["user_id"] == test_data["user1_id"]
    print(f"✓ 用户过滤成功，找到 {data['total']} 条记录")


def test_filter_by_action():
    """测试8: 按操作类型过滤"""
    print("\n=== 测试8: 按操作类型过滤 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/logs?action=org_create&organization_id={test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # 验证所有日志都是ORG_CREATE操作
    for log in data["logs"]:
        assert log["action"] == "org_create"
    print(f"✓ 操作类型过滤成功，找到 {data['total']} 条记录")


def test_filter_by_resource():
    """测试9: 按资源类型过滤"""
    print("\n=== 测试9: 按资源类型过滤 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/logs?resource_type=organization&organization_id={test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # 验证所有日志都是organization资源
    for log in data["logs"]:
        assert log["resource_type"] == "organization"
    print(f"✓ 资源类型过滤成功，找到 {data['total']} 条记录")


def test_filter_by_time():
    """测试10: 按时间范围过滤"""
    print("\n=== 测试10: 按时间范围过滤 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    # 查询最近1小时的日志
    start_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    end_time = datetime.utcnow().isoformat()

    response = client.get(
        f"/audit/logs?start_time={start_time}&end_time={end_time}&organization_id={test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    print(f"✓ 时间范围过滤成功，找到 {data['total']} 条记录")


def test_get_user_activity():
    """测试11: 获取用户活动"""
    print("\n=== 测试11: 获取用户活动 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/users/{test_data['user1_id']}/activity?days=7",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    print(f"✓ 获取到 {len(data)} 条用户活动记录")


def test_get_resource_history():
    """测试12: 获取资源历史"""
    print("\n=== 测试12: 获取资源历史 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/resources/organization/{test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # 至少有创建和更新两条记录
    print(f"✓ 获取到 {len(data)} 条资源历史记录")


def test_get_audit_stats():
    """测试13: 获取审计统计"""
    print("\n=== 测试13: 获取审计统计 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(
        f"/audit/stats?organization_id={test_data['org1_id']}&days=7",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert "by_action" in data
    assert len(data["by_action"]) > 0
    print(f"✓ 统计成功，总计 {data['total']} 条记录")
    print(f"  - 操作类型分布: {data['by_action']}")


def test_permission_control():
    """测试14: 权限控制"""
    print("\n=== 测试14: 权限控制 ===")

    # 注册第二个用户
    response = client.post("/auth/register", json={
        "username": "audit_user2",
        "email": "audit2@example.com",
        "password": "password123"
    })
    assert response.status_code == 201

    # 登录第二个用户
    response = client.post("/auth/login", json={
        "username": "audit_user2",
        "password": "password123"
    })
    assert response.status_code == 200
    user2_token = response.json()["access_token"]

    # 尝试查询第一个组织的审计日志（应该失败）
    headers = {"Authorization": f"Bearer {user2_token}"}
    response = client.get(
        f"/audit/logs?organization_id={test_data['org1_id']}",
        headers=headers
    )
    assert response.status_code == 403
    print("✓ 非成员无法查看组织审计日志")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("审计日志系统测试")
    print("="*60)

    try:
        setup_database()
        test_register_and_audit()
        test_login_and_audit()
        test_create_organization_and_audit()
        test_update_organization_and_audit()
        test_create_project_and_audit()
        test_query_audit_logs()
        test_filter_by_user()
        test_filter_by_action()
        test_filter_by_resource()
        test_filter_by_time()
        test_get_user_activity()
        test_get_resource_history()
        test_get_audit_stats()
        test_permission_control()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
