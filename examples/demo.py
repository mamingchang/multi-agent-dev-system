"""
Multi-Agent Development System
多Agent开发系统示例
"""
from src.orchestrator import Orchestrator
from src.workflow.task import Task


def main():
    """主函数"""
    print("=" * 80)
    print("多Agent开发系统演示")
    print("=" * 80)

    # 创建协调器
    orchestrator = Orchestrator(config={'max_iterations': 15})

    # 创建任务
    task = Task(
        task_id="TASK-001",
        title="开发用户管理系统",
        description="需要一个用户管理系统，支持用户注册、登录、权限管理等功能"
    )

    # 执行工作流
    result = orchestrator.execute_workflow(task)

    # 输出结果
    print("\n" + "=" * 80)
    print("最终结果:")
    print("=" * 80)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")

    if result['success']:
        task_data = result['task']
        print(f"\n任务详情:")
        print(f"  ID: {task_data['task_id']}")
        print(f"  标题: {task_data['title']}")
        print(f"  状态: {task_data['status']}")
        print(f"\n产物列表:")
        for artifact_name in task_data['artifacts'].keys():
            print(f"    - {artifact_name}")


if __name__ == "__main__":
    main()
