"""
测试向量检索系统

验证内容：
1. 向量存储基本操作
2. 语义记忆搜索
3. 语义经验搜索
4. 与现有系统集成
5. 相似度排序

注意：这些测试需要ChromaDB和Sentence Transformers
如果未安装，测试会跳过
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def check_vector_search_available():
    """检查向量搜索是否可用"""
    try:
        import chromadb
        import sentence_transformers
        return True
    except ImportError:
        return False


def test_vector_store():
    """测试1：向量存储基本操作"""
    print("\n" + "="*60)
    print("测试1：向量存储基本操作")
    print("="*60)

    if not check_vector_search_available():
        print("⚠️  ChromaDB未安装，跳过此测试")
        print("安装: pip install chromadb sentence-transformers")
        return

    from src.memory.vector_search import VectorStore

    # 创建向量存储
    store = VectorStore(
        collection_name="test_collection",
        persist_directory="./test_chroma_db"
    )

    print(f"✅ 向量存储创建成功")

    # 添加文档
    store.add(
        ids=["doc1", "doc2", "doc3"],
        documents=[
            "用户登录功能实现",
            "用户注册功能开发",
            "数据库设计和优化"
        ],
        metadatas=[
            {"type": "feature", "priority": "high"},
            {"type": "feature", "priority": "high"},
            {"type": "design", "priority": "medium"}
        ]
    )

    print(f"✅ 添加3个文档")
    print(f"✅ 文档数量: {store.count()}")

    # 查询相似文档
    results = store.query(
        query_texts=["登录系统"],
        n_results=2
    )

    print(f"\n查询'登录系统':")
    for i, doc_id in enumerate(results['ids'][0]):
        doc = results['documents'][0][i]
        distance = results['distances'][0][i]
        print(f"  {i+1}. {doc} (距离: {distance:.4f})")

    assert len(results['ids'][0]) == 2
    assert "doc1" in results['ids'][0]  # "用户登录功能实现"应该最相似

    # 清理
    import shutil
    shutil.rmtree("./test_chroma_db", ignore_errors=True)

    print("\n✅ 向量存储测试通过")


def test_semantic_memory_search():
    """测试2：语义记忆搜索"""
    print("\n" + "="*60)
    print("测试2：语义记忆搜索")
    print("="*60)

    if not check_vector_search_available():
        print("⚠️  ChromaDB未安装，跳过此测试")
        return

    from src.memory.vector_search import SemanticMemorySearch

    # 创建语义记忆搜索
    search = SemanticMemorySearch("TestAgent")

    # 添加记忆
    search.add_memory(
        memory_id="mem1",
        content="用户需要实现登录功能，使用JWT认证",
        metadata={"memory_type": "short_term", "importance": 3}
    )

    search.add_memory(
        memory_id="mem2",
        content="密码必须使用bcrypt进行哈希存储",
        metadata={"memory_type": "long_term", "importance": 4}
    )

    search.add_memory(
        memory_id="mem3",
        content="数据库使用PostgreSQL，需要设计用户表",
        metadata={"memory_type": "short_term", "importance": 2}
    )

    print(f"✅ 添加3条记忆")
    print(f"✅ 记忆数量: {search.count()}")

    # 语义搜索
    results = search.search_similar(
        query="如何实现用户认证",
        limit=2
    )

    print(f"\n搜索'如何实现用户认证':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['content']}")
        print(f"     相似度: {result['similarity']:.4f}")

    assert len(results) > 0
    # "用户需要实现登录功能"应该最相似
    assert "登录" in results[0]['content'] or "认证" in results[0]['content']

    # 清理
    import shutil
    shutil.rmtree("./chroma_db", ignore_errors=True)

    print("\n✅ 语义记忆搜索测试通过")


def test_semantic_experience_search():
    """测试3：语义经验搜索"""
    print("\n" + "="*60)
    print("测试3：语义经验搜索")
    print("="*60)

    if not check_vector_search_available():
        print("⚠️  ChromaDB未安装，跳过此测试")
        return

    from src.memory.vector_search import SemanticExperienceSearch

    # 创建语义经验搜索
    search = SemanticExperienceSearch()

    # 添加经验
    search.add_experience(
        experience_id="exp1",
        title="成功实现JWT认证",
        description="使用JWT token实现了用户认证，token有效期24小时",
        metadata={"experience_type": "success", "confidence": 0.9}
    )

    search.add_experience(
        experience_id="exp2",
        title="避免明文存储密码",
        description="绝不应该明文存储用户密码，必须使用bcrypt哈希",
        metadata={"experience_type": "anti_pattern", "confidence": 1.0}
    )

    search.add_experience(
        experience_id="exp3",
        title="数据库索引优化",
        description="为常用查询字段添加索引可以显著提升性能",
        metadata={"experience_type": "best_practice", "confidence": 0.8}
    )

    print(f"✅ 添加3条经验")
    print(f"✅ 经验数量: {search.count()}")

    # 语义搜索
    results = search.search_similar(
        query="用户登录安全性",
        limit=2
    )

    print(f"\n搜索'用户登录安全性':")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['document'][:50]}...")
        print(f"     相似度: {result['similarity']:.4f}")

    assert len(results) > 0

    # 清理
    import shutil
    shutil.rmtree("./chroma_db", ignore_errors=True)

    print("\n✅ 语义经验搜索测试通过")


def test_memory_system_integration():
    """测试4：与记忆系统集成"""
    print("\n" + "="*60)
    print("测试4：与记忆系统集成")
    print("="*60)

    if not check_vector_search_available():
        print("⚠️  ChromaDB未安装，跳过此测试")
        return

    from src.memory.memory_system import MemoryStore, MemoryType, MemoryImportance

    # 创建记忆存储
    store = MemoryStore("IntegrationAgent")

    # 添加记忆
    store.add_memory(
        content="实现用户登录功能，使用JWT认证",
        memory_type=MemoryType.SHORT_TERM,
        importance=MemoryImportance.HIGH,
        tags=["login", "jwt"]
    )

    store.add_memory(
        content="密码使用bcrypt哈希存储",
        memory_type=MemoryType.LONG_TERM,
        importance=MemoryImportance.CRITICAL,
        tags=["security", "password"]
    )

    store.add_memory(
        content="数据库使用PostgreSQL",
        memory_type=MemoryType.SHORT_TERM,
        importance=MemoryImportance.MEDIUM,
        tags=["database"]
    )

    print(f"✅ 添加3条记忆到记忆系统")

    # 使用语义搜索
    results = store.semantic_search(
        query="如何保证登录安全",
        limit=2
    )

    print(f"\n语义搜索'如何保证登录安全':")
    for i, memory in enumerate(results, 1):
        print(f"  {i}. {memory.content}")

    assert len(results) > 0

    # 清理
    import shutil
    shutil.rmtree("./chroma_db", ignore_errors=True)

    print("\n✅ 记忆系统集成测试通过")


def test_experience_system_integration():
    """测试5：与经验系统集成"""
    print("\n" + "="*60)
    print("测试5：与经验系统集成")
    print("="*60)

    if not check_vector_search_available():
        print("⚠️  ChromaDB未安装，跳过此测试")
        return

    from src.memory.retrospective import (
        ExperienceKnowledgeBase,
        Experience,
        ExperienceType
    )
    import uuid

    # 创建知识库
    kb = ExperienceKnowledgeBase()

    # 添加经验
    exp1 = Experience(
        experience_id=f"exp-{uuid.uuid4().hex[:12]}",
        experience_type=ExperienceType.SUCCESS,
        title="成功实现登录功能",
        description="使用JWT认证成功实现了登录功能，用户体验良好",
        context={'task': 'login'},
        agents_involved=['Developer'],
        tags=['success', 'login'],
        confidence=0.9
    )
    kb.add_experience(exp1)

    exp2 = Experience(
        experience_id=f"exp-{uuid.uuid4().hex[:12]}",
        experience_type=ExperienceType.BEST_PRACTICE,
        title="使用参数化查询防止SQL注入",
        description="数据库查询应该使用参数化查询，避免SQL注入攻击",
        context={'security': 'sql'},
        agents_involved=['Developer'],
        tags=['best_practice', 'security'],
        confidence=1.0
    )
    kb.add_experience(exp2)

    print(f"✅ 添加2条经验到知识库")

    # 使用语义搜索
    results = kb.semantic_search(
        query="如何防止安全漏洞",
        limit=2
    )

    print(f"\n语义搜索'如何防止安全漏洞':")
    for i, exp in enumerate(results, 1):
        print(f"  {i}. {exp.title}")
        print(f"     {exp.description}")

    assert len(results) > 0

    # 清理
    import shutil
    shutil.rmtree("./chroma_db", ignore_errors=True)

    print("\n✅ 经验系统集成测试通过")


def test_similarity_ranking():
    """测试6：相似度排序"""
    print("\n" + "="*60)
    print("测试6：相似度排序")
    print("="*60)

    if not check_vector_search_available():
        print("⚠️  ChromaDB未安装，跳过此测试")
        return

    from src.memory.vector_search import VectorStore

    store = VectorStore("ranking_test", "./test_chroma_db")

    # 添加不同相似度的文档
    store.add(
        ids=["doc1", "doc2", "doc3", "doc4"],
        documents=[
            "用户登录功能实现",           # 最相似
            "用户认证系统开发",           # 很相似
            "数据库设计和优化",           # 不太相似
            "前端界面美化"                # 不相似
        ]
    )

    # 查询
    results = store.query(
        query_texts=["登录认证"],
        n_results=4
    )

    print(f"\n查询'登录认证'的相似度排序:")
    for i in range(len(results['ids'][0])):
        doc = results['documents'][0][i]
        distance = results['distances'][0][i]
        similarity = 1 - distance
        print(f"  {i+1}. {doc}")
        print(f"     相似度: {similarity:.4f}")

    # 验证排序
    distances = results['distances'][0]
    assert distances[0] < distances[1] < distances[2] < distances[3]

    # 清理
    import shutil
    shutil.rmtree("./test_chroma_db", ignore_errors=True)

    print("\n✅ 相似度排序测试通过")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("向量检索系统测试")
    print("="*60)

    # 检查依赖
    vector_available = check_vector_search_available()
    if not vector_available:
        print("\n⚠️  警告: ChromaDB或Sentence Transformers未安装")
        print("部分测试将被跳过")
        print("安装: pip install chromadb sentence-transformers")

    try:
        # 测试1：向量存储
        test_vector_store()

        # 测试2：语义记忆搜索
        test_semantic_memory_search()

        # 测试3：语义经验搜索
        test_semantic_experience_search()

        # 测试4：记忆系统集成
        test_memory_system_integration()

        # 测试5：经验系统集成
        test_experience_system_integration()

        # 测试6：相似度排序
        test_similarity_ranking()

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有测试通过")
        print("\n关键验证点:")
        if vector_available:
            print("  ✅ 向量存储基本操作")
            print("  ✅ 语义记忆搜索")
            print("  ✅ 语义经验搜索")
            print("  ✅ 记忆系统集成")
            print("  ✅ 经验系统集成")
            print("  ✅ 相似度排序")
        else:
            print("  ⚠️  所有测试跳过（依赖未安装）")

        print("\n" + "="*60)
        print("使用说明")
        print("="*60)
        print("1. 安装依赖:")
        print("   pip install chromadb sentence-transformers")
        print("\n2. 使用语义搜索:")
        print("   # 记忆搜索")
        print("   memories = memory_store.semantic_search('登录功能', limit=5)")
        print("\n   # 经验搜索")
        print("   experiences = kb.semantic_search('安全最佳实践', limit=5)")
        print("\n3. 优势:")
        print("   - 理解语义相似性（'登录' ≈ 'sign in'）")
        print("   - 更智能的搜索结果")
        print("   - 按相似度排序")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
