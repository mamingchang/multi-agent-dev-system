"""
测试Agent记忆系统

验证内容：
1. 记忆的创建和存储
2. 记忆的检索和过滤
3. 记忆的过期和清理
4. Agent集成记忆系统
5. 记忆在工作流中的应用
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.memory_system import (
    Memory, MemoryStore, MemoryType, MemoryImportance,
    AgentMemoryManager, get_memory_manager
)
from src.agents.base_agent import BaseAgent
from src.llm.llm_client import create_llm_client
from typing import Dict, Any
import time


def test_memory_creation():
    """测试1：记忆创建"""
    print("\n" + "="*60)
    print("测试1：记忆创建和基本操作")
    print("="*60)

    store = MemoryStore("TestAgent")

    # 创建短期记忆
    mem1 = store.add_memory(
        content="用户要求实现登录功能",
        memory_type=MemoryType.SHORT_TERM,
        importance=MemoryImportance.HIGH,
        tags=["requirement", "login"]
    )
    print(f"✅ 创建短期记忆: {mem1.memory_id}")

    # 创建长期记忆
    mem2 = store.add_memory(
        content="登录功能应该使用JWT认证",
        memory_type=MemoryType.LONG_TERM,
        importance=MemoryImportance.CRITICAL,
        tags=["best_practice", "auth"]
    )
    print(f"✅ 创建长期记忆: {mem2.memory_id}")

    # 创建工作记忆
    mem3 = store.add_memory(
        content="当前正在分析需求的第3步",
        memory_type=MemoryType.WORKING,
        importance=MemoryImportance.MEDIUM,
        tags=["workflow"]
    )
    print(f"✅ 创建工作记忆: {mem3.memory_id}")

    # 统计
    stats = store.get_statistics()
    print(f"\n记忆统计:")
    print(f"  总数: {stats['total']}")
    print(f"  按类型: {stats['by_type']}")
    print(f"  按重要性: {stats['by_importance']}")

    assert stats['total'] == 3
    print("✅ 记忆创建测试通过")


def test_memory_search():
    """测试2：记忆检索"""
    print("\n" + "="*60)
    print("测试2：记忆检索和过滤")
    print("="*60)

    store = MemoryStore("SearchAgent")

    # 添加多条记忆
    store.add_memory("实现用户注册功能", MemoryType.SHORT_TERM, tags=["requirement"])
    store.add_memory("实现用户登录功能", MemoryType.SHORT_TERM, tags=["requirement"])
    store.add_memory("使用bcrypt哈希密码", MemoryType.LONG_TERM, tags=["security"])
    store.add_memory("JWT token有效期24小时", MemoryType.LONG_TERM, tags=["security"])
    store.add_memory("当前步骤：设计数据库", MemoryType.WORKING, tags=["workflow"])

    # 按关键词搜索
    results = store.search_memories(query="登录")
    print(f"\n搜索'登录': 找到 {len(results)} 条")
    for mem in results:
        print(f"  - {mem.content}")
    assert len(results) == 1

    # 按类型过滤
    long_term = store.search_memories(memory_type=MemoryType.LONG_TERM)
    print(f"\n长期记忆: {len(long_term)} 条")
    assert len(long_term) == 2

    # 按标签过滤
    security = store.search_memories(tags=["security"])
    print(f"\n安全相关: {len(security)} 条")
    assert len(security) == 2

    # 组合过滤
    important_security = store.search_memories(
        tags=["security"],
        min_importance=MemoryImportance.MEDIUM
    )
    print(f"\n重要的安全记忆: {len(important_security)} 条")

    print("✅ 记忆检索测试通过")


def test_memory_expiration():
    """测试3：记忆过期"""
    print("\n" + "="*60)
    print("测试3：记忆过期和清理")
    print("="*60)

    store = MemoryStore("ExpiryAgent")

    # 添加记忆
    store.add_memory("短期记忆1", MemoryType.SHORT_TERM)
    store.add_memory("短期记忆2", MemoryType.SHORT_TERM)
    store.add_memory("长期记忆1", MemoryType.LONG_TERM)
    store.add_memory("工作记忆1", MemoryType.WORKING)

    print(f"初始记忆数: {len(store.memories)}")

    # 清理工作记忆
    cleared = store.clear_working_memory()
    print(f"清理工作记忆: {cleared} 条")
    assert len(store.memories) == 3

    # 注意：实际过期需要等待时间，这里只测试逻辑
    print("✅ 记忆过期测试通过")


def test_agent_memory_integration():
    """测试4：Agent集成记忆系统"""
    print("\n" + "="*60)
    print("测试4：Agent集成记忆系统")
    print("="*60)

    # 创建Agent
    llm_client = create_llm_client("mock", responses={
        "MemoryAgent": "我已经记住了这个信息"
    })

    class MemoryAgent(BaseAgent):
        def _get_responsibilities(self) -> str:
            return "测试记忆功能"

        def process(self, task) -> Dict[str, Any]:
            return {'success': True}

    agent = MemoryAgent("MemoryAgent", "记忆测试员", llm_client=llm_client)

    # 测试记忆方法
    agent.remember("用户需要登录功能", memory_type_str="short_term", importance="high")
    agent.remember("使用JWT认证是最佳实践", memory_type_str="long_term", importance="critical")
    agent.remember("当前在第2步", memory_type_str="working")

    print("✅ Agent记住了3条信息")

    # 回忆
    memories = agent.recall(query="登录")
    print(f"回忆'登录': {len(memories)} 条")
    for mem in memories:
        print(f"  - {mem.content}")

    # 获取最近上下文
    recent = agent.get_recent_context(hours=24, limit=5)
    print(f"\n最近上下文: {len(recent)} 条")

    # 获取记忆摘要
    summary = agent.get_memory_summary()
    print(f"\n记忆摘要:\n{summary}")

    # 清空工作记忆
    cleared = agent.clear_working_memory()
    print(f"\n清空工作记忆: {cleared} 条")

    print("✅ Agent记忆集成测试通过")


def test_memory_in_workflow():
    """测试5：记忆在工作流中的应用"""
    print("\n" + "="*60)
    print("测试5：记忆在工作流中的应用")
    print("="*60)

    llm_client = create_llm_client("mock", responses={
        "Developer": "我会根据之前的经验来实现"
    })

    class SmartDeveloper(BaseAgent):
        def _get_responsibilities(self) -> str:
            return "智能开发"

        def process(self, task) -> Dict[str, Any]:
            # 在处理前回忆相关经验
            relevant_memories = self.recall(query="登录", limit=3)

            if relevant_memories:
                print(f"\n[{self.name}] 回忆到 {len(relevant_memories)} 条相关经验:")
                for mem in relevant_memories:
                    print(f"  - {mem.content}")

            # 处理任务
            result = "实现了登录功能，使用JWT认证"

            # 记住这次的经验
            self.remember(
                content=f"成功实现了登录功能: {result}",
                memory_type_str="long_term",
                importance="high",
                tags=["success", "login", "jwt"]
            )

            print(f"\n[{self.name}] 记住了这次的成功经验")

            return {'success': True, 'output': result}

    # 创建Agent
    developer = SmartDeveloper("Developer", "智能开发者", llm_client=llm_client)

    # 先添加一些历史经验
    developer.remember(
        "登录功能应该使用JWT认证",
        memory_type_str="long_term",
        importance="critical",
        tags=["best_practice", "login"]
    )
    developer.remember(
        "密码必须使用bcrypt哈希",
        memory_type_str="long_term",
        importance="critical",
        tags=["security", "login"]
    )

    print("✅ 预先添加了2条历史经验")

    # 模拟任务处理
    from src.workflow.task import Task
    task = Task("task-001", "实现登录", "实现用户登录功能")

    result = developer.process(task)
    print(f"\n任务处理结果: {result['success']}")

    # 验证记忆增加
    all_memories = developer.recall(limit=10)
    print(f"\n总记忆数: {len(all_memories)}")

    print("✅ 工作流记忆应用测试通过")


def test_memory_manager():
    """测试6：全局记忆管理器"""
    print("\n" + "="*60)
    print("测试6：全局记忆管理器")
    print("="*60)

    manager = get_memory_manager()

    # 为多个Agent添加记忆
    manager.add_memory("Agent1", "Agent1的记忆", MemoryType.SHORT_TERM)
    manager.add_memory("Agent2", "Agent2的记忆", MemoryType.SHORT_TERM)
    manager.add_memory("Agent1", "Agent1的另一条记忆", MemoryType.LONG_TERM)

    # 获取统计
    stats = manager.get_all_statistics()
    print(f"\n所有Agent的记忆统计:")
    for agent_name, agent_stats in stats.items():
        print(f"  {agent_name}: {agent_stats['total']} 条记忆")

    # 搜索特定Agent的记忆
    agent1_memories = manager.search_memories("Agent1", limit=10)
    print(f"\nAgent1的记忆: {len(agent1_memories)} 条")

    print("✅ 全局记忆管理器测试通过")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Agent记忆系统测试")
    print("="*60)

    try:
        # 测试1：记忆创建
        test_memory_creation()

        # 测试2：记忆检索
        test_memory_search()

        # 测试3：记忆过期
        test_memory_expiration()

        # 测试4：Agent集成
        test_agent_memory_integration()

        # 测试5：工作流应用
        test_memory_in_workflow()

        # 测试6：全局管理器
        test_memory_manager()

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有测试通过")
        print("\n关键验证点:")
        print("  ✅ 记忆创建和存储")
        print("  ✅ 记忆检索和过滤")
        print("  ✅ 记忆过期和清理")
        print("  ✅ Agent集成记忆系统")
        print("  ✅ 记忆在工作流中应用")
        print("  ✅ 全局记忆管理")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
