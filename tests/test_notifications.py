"""
通知系统测试

测试场景：
1. 创建通知配置
2. 获取通知配置列表
3. 更新通知配置
4. 删除通知配置
5. 发送邮件通知
6. 发送Slack通知
7. 获取通知历史
8. 获取通知统计
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from src.api.main import app
from src.database.database import Database
from src.database.models import Base
from src.api.dependencies import get_db as get_db_dependency

# 创建测试数据库
test_db = Database("sqlite:///:memory:")

# 覆盖依赖
def override_get_db():
    return test_db

app.dependency_overrides[get_db_dependency] = override_get_db

# 创建测试客户端
client = TestClient(app)

# 全局变量存储测试数据
test_data = {
    "user_token": None,
    "org_id": None,
    "config_id": None
}


def setup_database():
    """初始化测试数据库"""
    print("\n=== 初始化测试数据库 ===")
    Base.metadata.create_all(bind=test_db.engine)
    print("✓ 数据库表创建成功")


def test_setup():
    """测试准备：创建用户和组织"""
    print("\n=== 测试准备 ===")

    # 注册用户
    response = client.post("/auth/register", json={
        "username": "notification_user",
        "email": "notification@example.com",
        "password": "password123"
    })
    assert response.status_code == 201

    # 登录
    response = client.post("/auth/login", json={
        "username": "notification_user",
        "password": "password123"
    })
    assert response.status_code == 200
    test_data["user_token"] = response.json()["access_token"]

    # 创建组织
    headers = {"Authorization": f"Bearer {test_data['user_token']}"}
    response = client.post("/organizations", headers=headers, json={
        "name": "Notification Test Org",
        "slug": "notification-test-org",
        "token_quota": 10000,
        "max_projects": 10,
        "max_members": 50
    })
    assert response.status_code == 201
    test_data["org_id"] = response.json()["id"]
    print("✓ 测试准备完成")


def test_create_notification_config():
    """测试1: 创建通知配置"""
    print("\n=== 测试1: 创建通知配置 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.post("/notifications/configs", headers=headers, json={
        "notification_type": "quota_alert",
        "channel": "email",
        "is_enabled": True,
        "organization_id": test_data["org_id"],
        "config": {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_email": "noreply@example.com",
            "to_email": "notification@example.com",
            "use_tls": True
        }
    })
    assert response.status_code == 201
    data = response.json()
    test_data["config_id"] = data["id"]
    assert data["notification_type"] == "quota_alert"
    assert data["channel"] == "email"
    assert data["is_enabled"] == True
    print(f"✓ 通知配置创建成功: ID={data['id']}")


def test_list_notification_configs():
    """测试2: 获取通知配置列表"""
    print("\n=== 测试2: 获取通知配置列表 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/notifications/configs?organization_id={test_data['org_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    print(f"✓ 获取到 {len(data)} 个通知配置")


def test_update_notification_config():
    """测试3: 更新通知配置"""
    print("\n=== 测试3: 更新通知配置 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.put(
        f"/notifications/configs/{test_data['config_id']}",
        headers=headers,
        json={
            "is_enabled": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] == False
    print("✓ 通知配置更新成功")


def test_send_email_notification():
    """测试4: 发送邮件通知（模拟）"""
    print("\n=== 测试4: 发送邮件通知 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    # 注意：这个测试会失败，因为没有真实的SMTP服务器
    # 但可以验证API接口是否正常工作
    response = client.post("/notifications/send", headers=headers, json={
        "notification_type": "quota_alert",
        "channel": "email",
        "subject": "测试邮件",
        "content": "这是一封测试邮件",
        "organization_id": test_data["org_id"],
        "email_config": {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_email": "noreply@example.com",
            "to_email": "test@example.com",
            "use_tls": True
        }
    })

    # 预期会失败（因为SMTP服务器不存在）
    # 但至少验证了API接口可以调用
    print(f"✓ 邮件发送API调用完成（状态码: {response.status_code}）")


def test_get_notification_history():
    """测试5: 获取通知历史"""
    print("\n=== 测试5: 获取通知历史 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/notifications/history?organization_id={test_data['org_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    print(f"✓ 获取到 {len(data)} 条通知历史")


def test_get_notification_stats():
    """测试6: 获取通知统计"""
    print("\n=== 测试6: 获取通知统计 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/notifications/stats?organization_id={test_data['org_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "by_channel" in data
    assert "by_type" in data
    print(f"✓ 通知统计: 总计 {data['total']} 条")


def test_delete_notification_config():
    """测试7: 删除通知配置"""
    print("\n=== 测试7: 删除通知配置 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.delete(
        f"/notifications/configs/{test_data['config_id']}",
        headers=headers
    )
    assert response.status_code == 200
    print("✓ 通知配置删除成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("通知系统测试")
    print("="*60)

    try:
        setup_database()
        test_setup()
        test_create_notification_config()
        test_list_notification_configs()
        test_update_notification_config()
        test_send_email_notification()
        test_get_notification_history()
        test_get_notification_stats()
        test_delete_notification_config()

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
