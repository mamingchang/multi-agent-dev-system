"""
压力测试

使用Locust进行压力测试，测试系统在高负载下的表现。
"""

from locust import HttpUser, task, between, events
import random
import json


class MultiAgentUser(HttpUser):
    """多Agent系统用户"""

    # 等待时间（秒）
    wait_time = between(1, 3)

    def on_start(self):
        """初始化：登录获取token"""
        # 模拟登录
        response = self.client.post("/auth/login", json={
            "username": f"user_{random.randint(1, 1000)}",
            "password": "test123"
        })

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token", "")
        else:
            self.token = ""

    @task(3)
    def create_task(self):
        """创建任务（高频操作）"""
        headers = {"Authorization": f"Bearer {self.token}"}

        task_data = {
            "title": f"Test Task {random.randint(1, 10000)}",
            "description": "Automated stress test task",
            "project_id": random.randint(1, 10),
            "priority": random.randint(0, 100)
        }

        self.client.post(
            "/tasks",
            json=task_data,
            headers=headers,
            name="/tasks [CREATE]"
        )

    @task(5)
    def get_tasks(self):
        """获取任务列表（最高频操作）"""
        headers = {"Authorization": f"Bearer {self.token}"}

        self.client.get(
            f"/tasks?project_id={random.randint(1, 10)}",
            headers=headers,
            name="/tasks [LIST]"
        )

    @task(2)
    def get_task_detail(self):
        """获取任务详情"""
        headers = {"Authorization": f"Bearer {self.token}"}

        task_id = random.randint(1, 1000)
        self.client.get(
            f"/tasks/{task_id}",
            headers=headers,
            name="/tasks/{id} [GET]"
        )

    @task(1)
    def get_metrics(self):
        """获取监控指标"""
        headers = {"Authorization": f"Bearer {self.token}"}

        self.client.get(
            "/monitoring/metrics/system",
            headers=headers,
            name="/monitoring/metrics/system"
        )

    @task(1)
    def get_cost_stats(self):
        """获取成本统计"""
        headers = {"Authorization": f"Bearer {self.token}"}

        org_id = random.randint(1, 10)
        self.client.get(
            f"/cost/organization/{org_id}",
            headers=headers,
            name="/cost/organization/{id}"
        )


# ============================================================================
# 事件处理
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始"""
    print("\n" + "="*60)
    print("压力测试开始")
    print("="*60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束"""
    print("\n" + "="*60)
    print("压力测试结束")
    print("="*60)

    # 打印统计信息
    stats = environment.stats
    print(f"\n总请求数: {stats.total.num_requests}")
    print(f"失败请求数: {stats.total.num_failures}")
    print(f"平均响应时间: {stats.total.avg_response_time:.2f}ms")
    print(f"最大响应时间: {stats.total.max_response_time:.2f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")


# ============================================================================
# 压力测试场景
# ============================================================================

class HighConcurrencyUser(HttpUser):
    """高并发场景用户"""

    wait_time = between(0.1, 0.5)  # 更短的等待时间

    def on_start(self):
        """初始化"""
        self.token = "test_token"

    @task
    def rapid_requests(self):
        """快速请求"""
        headers = {"Authorization": f"Bearer {self.token}"}

        # 快速连续请求
        for _ in range(10):
            self.client.get(
                "/health",
                headers=headers,
                name="/health [RAPID]"
            )


class DatabaseStressUser(HttpUser):
    """数据库压力场景用户"""

    wait_time = between(0.5, 1)

    def on_start(self):
        """初始化"""
        self.token = "test_token"

    @task
    def complex_query(self):
        """复杂查询"""
        headers = {"Authorization": f"Bearer {self.token}"}

        # 模拟复杂查询
        self.client.get(
            "/tasks?status=completed&sort=created_at&limit=100",
            headers=headers,
            name="/tasks [COMPLEX_QUERY]"
        )

    @task
    def batch_create(self):
        """批量创建"""
        headers = {"Authorization": f"Bearer {self.token}"}

        # 批量创建任务
        tasks = [
            {
                "title": f"Batch Task {i}",
                "description": "Batch test",
                "project_id": 1
            }
            for i in range(10)
        ]

        for task_data in tasks:
            self.client.post(
                "/tasks",
                json=task_data,
                headers=headers,
                name="/tasks [BATCH_CREATE]"
            )


# ============================================================================
# 运行说明
# ============================================================================

"""
运行压力测试：

1. 基础压力测试（100并发用户）：
   locust -f tests/test_stress.py --users 100 --spawn-rate 10 --run-time 5m

2. 高并发测试（1000并发用户）：
   locust -f tests/test_stress.py --users 1000 --spawn-rate 50 --run-time 10m

3. 数据库压力测试：
   locust -f tests/test_stress.py --users 500 --spawn-rate 25 --run-time 10m DatabaseStressUser

4. Web界面测试：
   locust -f tests/test_stress.py
   然后访问 http://localhost:8089

测试指标：
- RPS (Requests Per Second): 每秒请求数
- 响应时间: 平均、P50、P95、P99
- 错误率: 失败请求占比
- 并发数: 同时活跃的用户数
"""
