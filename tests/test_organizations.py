"""
组织管理系统测试

测试场景：
1. 创建组织
2. 获取组织列表
3. 获取组织详情
4. 更新组织
5. 删除组织
6. 获取配额信息
7. 添加组织成员
8. 获取成员列表
9. 更新成员角色
10. 移除成员
11. 权限控制测试
12. 数据隔离测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from src.api.main import app
from src.database.database import Database
from src.database.models import Base

# 创建测试客户端
client = TestClient(app)

# 测试数据库
test_db = Database("sqlite:///:memory:")

# 全局变量存储测试数据
test_data = {
    "user1_token": None,
    "user2_token": None,
    "org1_id": None,
    "org2_id": None,
    "project1_id": None
}


def setup_database():
    """初始化测试数据库"""
    print("\n=== 初始化测试数据库 ===")
    Base.metadata.create_all(bind=test_db.engine)
    print("✓ 数据库表创建成功")


def test_register_users():
    """测试用户注册"""
    print("\n=== 测试1: 用户注册 ===")

    # 注册用户1
    response = client.post("/auth/register", json={
        "username": "org_admin",
        "email": "admin@example.com",
        "password": "password123",
        "full_name": "Organization Admin"
    })
    assert response.status_code == 201
    print("✓ 用户1注册成功")

    # 注册用户2
    response = client.post("/auth/register", json={
        "username": "org_member",
        "email": "member@example.com",
        "password": "password123",
        "full_name": "Organization Member"
    })
    assert response.status_code == 201
    print("✓ 用户2注册成功")


def test_login_users():
    """测试用户登录"""
    print("\n=== 测试2: 用户登录 ===")

    # 用户1登录
    response = client.post("/auth/login", json={
        "username": "org_admin",
        "password": "password123"
    })
    assert response.status_code == 200
    test_data["user1_token"] = response.json()["access_token"]
    print("✓ 用户1登录成功")

    # 用户2登录
    response = client.post("/auth/login", json={
        "username": "org_member",
        "password": "password123"
    })
    assert response.status_code == 200
    test_data["user2_token"] = response.json()["access_token"]
    print("✓ 用户2登录成功")


def test_create_organization():
    """测试创建组织"""
    print("\n=== 测试3: 创建组织 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    # 创建组织1
    response = client.post("/organizations", headers=headers, json={
        "name": "Tech Company",
        "slug": "tech-company",
        "description": "A technology company",
        "token_quota": 2000000,
        "max_projects": 20,
        "max_members": 100
    })
    assert response.status_code == 201
    data = response.json()
    test_data["org1_id"] = data["id"]
    assert data["name"] == "Tech Company"
    assert data["slug"] == "tech-company"
    assert data["token_quota"] == 2000000
    assert data["token_used"] == 0
    print(f"✓ 组织1创建成功 (ID: {data['id']})")

    # 创建组织2
    response = client.post("/organizations", headers=headers, json={
        "name": "Startup Inc",
        "slug": "startup-inc",
        "description": "A startup company"
    })
    assert response.status_code == 201
    data = response.json()
    test_data["org2_id"] = data["id"]
    print(f"✓ 组织2创建成功 (ID: {data['id']})")


def test_list_organizations():
    """测试获取组织列表"""
    print("\n=== 测试4: 获取组织列表 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get("/organizations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    print(f"✓ 获取到 {len(data)} 个组织")


def test_get_organization():
    """测试获取组织详情"""
    print("\n=== 测试5: 获取组织详情 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(f"/organizations/{test_data['org1_id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tech Company"
    assert data["slug"] == "tech-company"
    print("✓ 组织详情获取成功")


def test_update_organization():
    """测试更新组织"""
    print("\n=== 测试6: 更新组织 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.put(f"/organizations/{test_data['org1_id']}", headers=headers, json={
        "name": "Tech Company Updated",
        "description": "Updated description",
        "token_quota": 3000000
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tech Company Updated"
    assert data["token_quota"] == 3000000
    print("✓ 组织更新成功")


def test_get_quota():
    """测试获取配额信息"""
    print("\n=== 测试7: 获取配额信息 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(f"/organizations/{test_data['org1_id']}/quota", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["token_quota"] == 3000000
    assert data["token_used"] == 0
    assert data["token_remaining"] == 3000000
    assert data["usage_percentage"] == 0.0
    assert data["current_projects"] == 0
    assert data["current_members"] == 1  # 创建者
    print("✓ 配额信息获取成功")
    print(f"  - Token配额: {data['token_quota']}")
    print(f"  - 已使用: {data['token_used']}")
    print(f"  - 使用率: {data['usage_percentage']}%")


def test_add_member():
    """测试添加组织成员"""
    print("\n=== 测试8: 添加组织成员 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    # 获取用户2的ID
    response = client.post("/auth/login", json={
        "username": "org_member",
        "password": "password123"
    })
    user2_id = response.json()["user"]["id"]

    # 添加用户2为成员
    response = client.post(
        f"/organizations/{test_data['org1_id']}/members",
        headers=headers,
        json={
            "user_id": user2_id,
            "role": "org_member"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user2_id
    assert data["role"] == "org_member"
    print("✓ 成员添加成功")


def test_list_members():
    """测试获取成员列表"""
    print("\n=== 测试9: 获取成员列表 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.get(f"/organizations/{test_data['org1_id']}/members", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # 创建者 + 新成员
    print(f"✓ 获取到 {len(data)} 个成员")


def test_update_member_role():
    """测试更新成员角色"""
    print("\n=== 测试10: 更新成员角色 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    # 获取用户2的ID
    response = client.post("/auth/login", json={
        "username": "org_member",
        "password": "password123"
    })
    user2_id = response.json()["user"]["id"]

    # 更新用户2为管理员
    response = client.put(
        f"/organizations/{test_data['org1_id']}/members/{user2_id}",
        headers=headers,
        json={
            "role": "org_admin"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "org_admin"
    print("✓ 成员角色更新成功")


def test_permission_control():
    """测试权限控制"""
    print("\n=== 测试11: 权限控制 ===")

    # 用户2现在是管理员，应该可以更新组织
    headers = {"Authorization": f"Bearer {test_data['user2_token']}"}

    response = client.put(f"/organizations/{test_data['org1_id']}", headers=headers, json={
        "description": "Updated by admin"
    })
    assert response.status_code == 200
    print("✓ 管理员权限验证成功")

    # 用户2不应该能访问组织2（不是成员）
    response = client.get(f"/organizations/{test_data['org2_id']}", headers=headers)
    assert response.status_code == 403
    print("✓ 非成员访问限制验证成功")


def test_create_project_with_organization():
    """测试在组织下创建项目"""
    print("\n=== 测试12: 在组织下创建项目 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    response = client.post("/projects", headers=headers, json={
        "name": "Project Alpha",
        "description": "First project",
        "organization_id": test_data["org1_id"]
    })
    assert response.status_code == 201
    data = response.json()
    test_data["project1_id"] = data["id"]
    print(f"✓ 项目创建成功 (ID: {data['id']})")

    # 验证配额中的项目数增加
    response = client.get(f"/organizations/{test_data['org1_id']}/quota", headers=headers)
    data = response.json()
    assert data["current_projects"] == 1
    print("✓ 项目计数更新成功")


def test_remove_member():
    """测试移除成员"""
    print("\n=== 测试13: 移除成员 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    # 获取用户2的ID
    response = client.post("/auth/login", json={
        "username": "org_member",
        "password": "password123"
    })
    user2_id = response.json()["user"]["id"]

    # 移除用户2
    response = client.delete(
        f"/organizations/{test_data['org1_id']}/members/{user2_id}",
        headers=headers
    )
    assert response.status_code == 204
    print("✓ 成员移除成功")

    # 验证成员列表
    response = client.get(f"/organizations/{test_data['org1_id']}/members", headers=headers)
    data = response.json()
    assert len(data) == 1  # 只剩创建者
    print("✓ 成员列表验证成功")


def test_delete_organization():
    """测试删除组织"""
    print("\n=== 测试14: 删除组织 ===")

    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}

    # 删除组织2
    response = client.delete(f"/organizations/{test_data['org2_id']}", headers=headers)
    assert response.status_code == 204
    print("✓ 组织删除成功")

    # 验证组织列表
    response = client.get("/organizations", headers=headers)
    data = response.json()
    assert len(data) == 1  # 只剩组织1
    print("✓ 组织列表验证成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("组织管理系统测试")
    print("="*60)

    try:
        setup_database()
        test_register_users()
        test_login_users()
        test_create_organization()
        test_list_organizations()
        test_get_organization()
        test_update_organization()
        test_get_quota()
        test_add_member()
        test_list_members()
        test_update_member_role()
        test_permission_control()
        test_create_project_with_organization()
        test_remove_member()
        test_delete_organization()

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
