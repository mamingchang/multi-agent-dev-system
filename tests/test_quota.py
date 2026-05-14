"""
配额管理系统测试

测试场景：
1. 记录配额使用
2. 获取配额统计
3. 获取每日使用量
4. 获取用户使用统计
5. 获取配额信息
6. 配额超限检查
7. 配额告警（80%警告）
8. 配额告警（90%严重）
9. 配额告警（100%超限）
10. 创建限流配置
11. 获取限流配置列表
12. 更新限流配置
13. 删除限流配置
14. 获取告警列表
15. 解决告警
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from src.api.main import app
from src.database.database import Database
from src.database.models import Base
from src.database.quota_repository import QuotaUsageRepository
from src.database.organization_repository import OrganizationRepository
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
    "org_id": None
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
        "username": "quota_user",
        "email": "quota@example.com",
        "password": "password123"
    })
    assert response.status_code == 201

    # 登录
    response = client.post("/auth/login", json={
        "username": "quota_user",
        "password": "password123"
    })
    assert response.status_code == 200
    test_data["user_token"] = response.json()["access_token"]

    # 创建组织（配额10000 tokens）
    headers = {"Authorization": f"Bearer {test_data['user_token']}"}
    response = client.post("/organizations", headers=headers, json={
        "name": "Quota Test Org",
        "slug": "quota-test-org",
        "token_quota": 10000,
        "max_projects": 10,
        "max_members": 50
    })
    assert response.status_code == 201
    test_data["org_id"] = response.json()["id"]
    print("✓ 测试准备完成")


def test_record_usage():
    """测试1: 记录配额使用"""
    print("\n=== 测试1: 记录配额使用 ===")

    # 使用测试数据库
    with test_db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        # 记录使用
        usage_repo.record_usage(
            organization_id=test_data["org_id"],
            tokens_used=1000,
            api_calls=1,
            resource_type="task",
            resource_id="task-1"
        )

        print("✓ 配额使用记录成功")


def test_get_usage_stats():
    """测试2: 获取配额统计"""
    print("\n=== 测试2: 获取配额统计 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/quota/usage?organization_id={test_data['org_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_tokens"] == 1000
    assert data["total_calls"] == 1
    print(f"✓ 统计成功: {data['total_tokens']} tokens, {data['total_calls']} calls")


def test_get_daily_usage():
    """测试3: 获取每日使用量"""
    print("\n=== 测试3: 获取每日使用量 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/quota/usage/daily?organization_id={test_data['org_id']}&days=7",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    print(f"✓ 获取到 {len(data)} 天的使用数据")


def test_get_quota_info():
    """测试4: 获取配额信息"""
    print("\n=== 测试4: 获取配额信息 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/quota/info?organization_id={test_data['org_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_quota"] == 10000
    assert data["token_used"] == 1000
    assert data["token_remaining"] == 9000
    assert data["usage_percentage"] == 10.0
    print(f"✓ 配额信息: {data['usage_percentage']}% 已使用")


def test_quota_warning_alert():
    """测试5: 配额告警（80%警告）"""
    print("\n=== 测试5: 配额告警（80%警告） ===")

    with test_db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        # 使用到80%（8000 tokens）
        usage_repo.record_usage(
            organization_id=test_data["org_id"],
            tokens_used=7000,  # 总共8000
            api_calls=1
        )

    # 检查告警
    headers = {"Authorization": f"Bearer {test_data['user_token']}"}
    response = client.get(
        f"/quota/alerts?organization_id={test_data['org_id']}&resolved=false",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["alert_level"] == "warning"
    print(f"✓ 警告告警已触发: {data[0]['message']}")


def test_quota_critical_alert():
    """测试6: 配额告警（90%严重）"""
    print("\n=== 测试6: 配额告警（90%严重） ===")

    with test_db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        # 使用到90%（9000 tokens）
        usage_repo.record_usage(
            organization_id=test_data["org_id"],
            tokens_used=1000,  # 总共9000
            api_calls=1
        )

    # 检查告警
    headers = {"Authorization": f"Bearer {test_data['user_token']}"}
    response = client.get(
        f"/quota/alerts?organization_id={test_data['org_id']}&resolved=false",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    # 应该有2个告警：warning和critical
    assert len(data) >= 2
    critical_alerts = [a for a in data if a["alert_level"] == "critical"]
    assert len(critical_alerts) >= 1
    print(f"✓ 严重告警已触发: {critical_alerts[0]['message']}")


def test_quota_exceeded_alert():
    """测试7: 配额告警（100%超限）"""
    print("\n=== 测试7: 配额告警（100%超限） ===")

    with test_db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        # 使用到100%（10000 tokens）
        usage_repo.record_usage(
            organization_id=test_data["org_id"],
            tokens_used=1000,  # 总共10000
            api_calls=1
        )

    # 检查告警
    headers = {"Authorization": f"Bearer {test_data['user_token']}"}
    response = client.get(
        f"/quota/alerts?organization_id={test_data['org_id']}&resolved=false",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    exceeded_alerts = [a for a in data if a["alert_level"] == "exceeded"]
    assert len(exceeded_alerts) >= 1
    print(f"✓ 超限告警已触发: {exceeded_alerts[0]['message']}")


def test_create_rate_limit():
    """测试8: 创建限流配置"""
    print("\n=== 测试8: 创建限流配置 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.post("/quota/rate-limits", headers=headers, json={
        "max_requests": 100,
        "period": "minute",
        "organization_id": test_data["org_id"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["max_requests"] == 100
    assert data["period"] == "minute"
    print("✓ 限流配置创建成功")


def test_list_rate_limits():
    """测试9: 获取限流配置列表"""
    print("\n=== 测试9: 获取限流配置列表 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    response = client.get(
        f"/quota/rate-limits?organization_id={test_data['org_id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    print(f"✓ 获取到 {len(data)} 个限流配置")


def test_resolve_alert():
    """测试10: 解决告警"""
    print("\n=== 测试10: 解决告警 ===")

    headers = {"Authorization": f"Bearer {test_data['user_token']}"}

    # 获取第一个未解决的告警
    response = client.get(
        f"/quota/alerts?organization_id={test_data['org_id']}&resolved=false",
        headers=headers
    )
    data = response.json()
    if len(data) > 0:
        alert_id = data[0]["id"]

        # 解决告警
        response = client.post(
            f"/quota/alerts/{alert_id}/resolve",
            headers=headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["is_resolved"] == True
        print("✓ 告警已解决")
    else:
        print("✓ 没有未解决的告警")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("配额管理系统测试")
    print("="*60)

    try:
        setup_database()
        test_setup()
        test_record_usage()
        test_get_usage_stats()
        test_get_daily_usage()
        test_get_quota_info()
        test_quota_warning_alert()
        test_quota_critical_alert()
        test_quota_exceeded_alert()
        test_create_rate_limit()
        test_list_rate_limits()
        test_resolve_alert()

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
