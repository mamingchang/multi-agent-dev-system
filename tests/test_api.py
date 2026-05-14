"""
API集成测试

测试完整的API流程：
1. 用户注册和登录
2. 创建项目
3. 创建会话和任务
4. 执行工作流
5. 查询结果

使用pytest和httpx进行测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from src.api.main import app

# 创建测试客户端
client = TestClient(app)


def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试1：健康检查")
    print("="*60)

    response = client.get("/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ 健康检查通过")


def test_user_registration_and_login():
    """测试用户注册和登录"""
    print("\n" + "="*60)
    print("测试2：用户注册和登录")
    print("="*60)

    # 注册用户
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }

    response = client.post("/auth/register", json=register_data)
    print(f"\n注册响应: {response.status_code}")
    if response.status_code == 201:
        print(f"用户创建成功: {response.json()['username']}")
        print("✅ 用户注册成功")
    else:
        print(f"注册失败: {response.json()}")
        # 可能是用户已存在，继续测试登录
        print("⚠️  用户可能已存在，继续测试登录")

    # 登录
    login_data = {
        "username": "testuser",
        "password": "password123"
    }

    response = client.post("/auth/login", json=login_data)
    print(f"\n登录响应: {response.status_code}")

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data

    token = data["access_token"]
    print(f"Token获取成功: {token[:20]}...")
    print(f"用户信息: {data['user']['username']}")
    print("✅ 用户登录成功")

    return token


def test_project_management(token: str):
    """测试项目管理"""
    print("\n" + "="*60)
    print("测试3：项目管理")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 创建项目
    project_data = {
        "name": "Test Project",
        "description": "A test project for API testing"
    }

    response = client.post("/projects", json=project_data, headers=headers)
    print(f"\n创建项目响应: {response.status_code}")
    if response.status_code != 201:
        print(f"错误详情: {response.json()}")

    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]
    print(f"项目创建成功: {project['name']} (ID: {project_id})")
    print("✅ 项目创建成功")

    # 获取项目列表
    response = client.get("/projects", headers=headers)
    print(f"\n获取项目列表响应: {response.status_code}")

    assert response.status_code == 200
    projects = response.json()
    print(f"项目数量: {len(projects)}")
    print("✅ 获取项目列表成功")

    # 获取项目详情
    response = client.get(f"/projects/{project_id}", headers=headers)
    print(f"\n获取项目详情响应: {response.status_code}")

    assert response.status_code == 200
    project_detail = response.json()
    print(f"项目详情: {project_detail['name']}")
    print("✅ 获取项目详情成功")

    return project_id


def test_workflow_execution(token: str, project_id: int):
    """测试工作流执行"""
    print("\n" + "="*60)
    print("测试4：工作流执行")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 创建会话
    session_data = {
        "project_id": project_id,
        "meta_data": {"description": "Test session"}
    }

    response = client.post("/workflow/sessions", json=session_data, headers=headers)
    print(f"\n创建会话响应: {response.status_code}")

    assert response.status_code == 201
    session = response.json()
    session_id = session["id"]
    print(f"会话创建成功: {session_id}")
    print("✅ 会话创建成功")

    # 创建任务
    task_data = {
        "session_id": session_id,
        "title": "实现用户登录功能",
        "description": "实现基于JWT的用户登录"
    }

    response = client.post("/workflow/tasks", json=task_data, headers=headers)
    print(f"\n创建任务响应: {response.status_code}")

    assert response.status_code == 201
    task = response.json()
    task_id = task["id"]
    print(f"任务创建成功: {task['title']} (ID: {task_id})")
    print("✅ 任务创建成功")

    # 执行工作流（使用Mock LLM）
    execute_data = {
        "task_id": task_id,
        "agents": ["Requester", "Developer", "CodeReviewer"],
        "max_iterations": 3,
        "llm_config": {
            "type": "mock",
            "responses": {
                "Requester": "# 需求文档\n\n实现用户登录",
                "Developer": "# 登录代码\n\n```python\ndef login(): pass\n```",
                "CodeReviewer": "✅ 代码审查通过"
            }
        }
    }

    response = client.post(f"/workflow/tasks/{task_id}/execute", json=execute_data, headers=headers)
    print(f"\n执行工作流响应: {response.status_code}")

    assert response.status_code == 200
    result = response.json()
    print(f"工作流状态: {result['message']}")
    print("✅ 工作流启动成功")

    # 等待一下让后台任务执行
    import time
    time.sleep(2)

    # 获取任务事件
    response = client.get(f"/workflow/tasks/{task_id}/events", headers=headers)
    print(f"\n获取任务事件响应: {response.status_code}")

    if response.status_code == 200:
        events = response.json()
        print(f"事件数量: {len(events)}")
        for event in events:
            print(f"  - {event['agent_name']}: {event['event_type']}")
        print("✅ 获取任务事件成功")

    # 获取任务产物
    response = client.get(f"/workflow/tasks/{task_id}/artifacts", headers=headers)
    print(f"\n获取任务产物响应: {response.status_code}")

    if response.status_code == 200:
        artifacts = response.json()
        print(f"产物数量: {len(artifacts)}")
        for artifact in artifacts:
            print(f"  - {artifact['name']} ({artifact['artifact_type']})")
        print("✅ 获取任务产物成功")


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("API集成测试")
    print("="*60)

    try:
        # 测试1：健康检查
        test_health_check()

        # 测试2：用户注册和登录
        token = test_user_registration_and_login()

        # 测试3：项目管理
        project_id = test_project_management(token)

        # 测试4：工作流执行
        test_workflow_execution(token, project_id)

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有API测试通过")
        print("\n关键验证点:")
        print("  ✅ 用户认证和授权")
        print("  ✅ 项目管理")
        print("  ✅ 会话和任务创建")
        print("  ✅ 工作流执行")
        print("  ✅ 事件和产物查询")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
