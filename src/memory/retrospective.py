"""
经验回溯系统（Retrospective System）

实现任务复盘和经验提取，让系统能够从历史任务中学习。

核心功能：
1. 任务执行日志分析
2. 成功/失败模式识别
3. 最佳实践提取
4. 错误分析和改进建议
5. 经验知识库管理

设计原则：
- 自动化：任务完成后自动触发复盘
- 结构化：提取的经验以结构化方式存储
- 可查询：支持按场景、Agent、问题类型查询
- 持续改进：经验会影响后续任务的执行

为什么需要经验回溯：
- 避免重复错误：记住失败的教训
- 复用成功经验：相似场景使用验证过的方案
- 持续优化：系统随着使用变得更智能
- 知识积累：构建领域知识库
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class ExperienceType(Enum):
    """经验类型"""
    SUCCESS = "success"          # 成功经验
    FAILURE = "failure"          # 失败教训
    BEST_PRACTICE = "best_practice"  # 最佳实践
    ANTI_PATTERN = "anti_pattern"    # 反模式
    OPTIMIZATION = "optimization"    # 优化建议


class Experience:
    """
    经验对象

    表示从任务中提取的一条经验。
    """

    def __init__(
        self,
        experience_id: str,
        experience_type: ExperienceType,
        title: str,
        description: str,
        context: Dict[str, Any],
        agents_involved: List[str],
        tags: List[str] = None,
        confidence: float = 1.0
    ):
        self.experience_id = experience_id
        self.experience_type = experience_type
        self.title = title
        self.description = description
        self.context = context  # 场景上下文
        self.agents_involved = agents_involved
        self.tags = tags or []
        self.confidence = confidence  # 置信度（0-1）
        self.created_at = datetime.now()
        self.applied_count = 0  # 被应用次数
        self.success_rate = 0.0  # 应用成功率

    def apply(self, success: bool):
        """
        记录经验被应用

        Args:
            success: 应用是否成功
        """
        self.applied_count += 1
        if success:
            self.success_rate = (
                (self.success_rate * (self.applied_count - 1) + 1.0) / self.applied_count
            )
        else:
            self.success_rate = (
                (self.success_rate * (self.applied_count - 1)) / self.applied_count
            )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'experience_id': self.experience_id,
            'experience_type': self.experience_type.value,
            'title': self.title,
            'description': self.description,
            'context': self.context,
            'agents_involved': self.agents_involved,
            'tags': self.tags,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'applied_count': self.applied_count,
            'success_rate': self.success_rate
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experience':
        """从字典创建"""
        exp = cls(
            experience_id=data['experience_id'],
            experience_type=ExperienceType(data['experience_type']),
            title=data['title'],
            description=data['description'],
            context=data['context'],
            agents_involved=data['agents_involved'],
            tags=data.get('tags', []),
            confidence=data.get('confidence', 1.0)
        )
        exp.created_at = datetime.fromisoformat(data['created_at'])
        exp.applied_count = data.get('applied_count', 0)
        exp.success_rate = data.get('success_rate', 0.0)
        return exp


class TaskRetrospective:
    """
    任务复盘

    分析单个任务的执行情况，提取经验。
    """

    def __init__(self, task_id: str, task_title: str):
        self.task_id = task_id
        self.task_title = task_title
        self.events: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.iteration_count: Dict[str, int] = {}
        self.success: bool = False
        self.duration: float = 0.0

    def add_event(self, event: Dict[str, Any]):
        """添加事件"""
        self.events.append(event)

    def add_artifact(self, artifact: Dict[str, Any]):
        """添加产物"""
        self.artifacts.append(artifact)

    def analyze(self) -> List[Experience]:
        """
        分析任务，提取经验

        Returns:
            List[Experience]: 提取的经验列表
        """
        experiences = []

        # 分析迭代次数
        experiences.extend(self._analyze_iterations())

        # 分析成功/失败模式
        if self.success:
            experiences.extend(self._analyze_success_patterns())
        else:
            experiences.extend(self._analyze_failure_patterns())

        # 分析Agent协作
        experiences.extend(self._analyze_collaboration())

        return experiences

    def _analyze_iterations(self) -> List[Experience]:
        """分析迭代次数，识别问题"""
        experiences = []
        import uuid

        for agent_name, count in self.iteration_count.items():
            if count > 3:
                # 迭代次数过多，可能有问题
                exp = Experience(
                    experience_id=f"exp-{uuid.uuid4().hex[:12]}",
                    experience_type=ExperienceType.ANTI_PATTERN,
                    title=f"{agent_name}迭代次数过多",
                    description=f"{agent_name}在任务'{self.task_title}'中迭代了{count}次，可能存在问题",
                    context={
                        'task_id': self.task_id,
                        'agent': agent_name,
                        'iteration_count': count
                    },
                    agents_involved=[agent_name],
                    tags=['iteration', 'performance', agent_name.lower()],
                    confidence=0.8
                )
                experiences.append(exp)

        return experiences

    def _analyze_success_patterns(self) -> List[Experience]:
        """分析成功模式"""
        experiences = []
        import uuid

        # 如果任务成功且迭代少，记录为最佳实践
        total_iterations = sum(self.iteration_count.values())
        if total_iterations <= len(self.iteration_count) * 2:
            exp = Experience(
                experience_id=f"exp-{uuid.uuid4().hex[:12]}",
                experience_type=ExperienceType.SUCCESS,
                title=f"高效完成任务：{self.task_title}",
                description=f"任务成功完成，总迭代次数{total_iterations}，效率较高",
                context={
                    'task_id': self.task_id,
                    'iteration_count': self.iteration_count,
                    'duration': self.duration
                },
                agents_involved=list(self.iteration_count.keys()),
                tags=['success', 'efficient'],
                confidence=0.9
            )
            experiences.append(exp)

        return experiences

    def _analyze_failure_patterns(self) -> List[Experience]:
        """分析失败模式"""
        experiences = []
        import uuid

        # 记录失败教训
        exp = Experience(
            experience_id=f"exp-{uuid.uuid4().hex[:12]}",
            experience_type=ExperienceType.FAILURE,
            title=f"任务失败：{self.task_title}",
            description=f"任务未能完成，需要分析原因",
            context={
                'task_id': self.task_id,
                'iteration_count': self.iteration_count
            },
            agents_involved=list(self.iteration_count.keys()),
            tags=['failure'],
            confidence=1.0
        )
        experiences.append(exp)

        return experiences

    def _analyze_collaboration(self) -> List[Experience]:
        """分析Agent协作模式"""
        experiences = []
        # 这里可以添加更复杂的协作模式分析
        return experiences


class ExperienceKnowledgeBase:
    """
    经验知识库

    存储和管理所有提取的经验。
    """

    def __init__(self):
        self.experiences: Dict[str, Experience] = {}

    def add_experience(self, experience: Experience):
        """添加经验"""
        self.experiences[experience.experience_id] = experience

        # 同步到向量存储（如果可用）
        try:
            from .vector_search import get_semantic_experience_search
            vector_search = get_semantic_experience_search()
            vector_search.add_experience(
                experience_id=experience.experience_id,
                title=experience.title,
                description=experience.description,
                metadata={
                    'experience_type': experience.experience_type.value,
                    'confidence': experience.confidence,
                    'agents_involved': experience.agents_involved,
                    'tags': experience.tags,
                    'created_at': experience.created_at.isoformat()
                }
            )
        except ImportError:
            # 向量搜索不可用，跳过
            pass

    def search_experiences(
        self,
        query: str = None,
        experience_type: ExperienceType = None,
        agents: List[str] = None,
        tags: List[str] = None,
        min_confidence: float = 0.0,
        min_success_rate: float = 0.0,
        limit: int = 10
    ) -> List[Experience]:
        """
        搜索经验

        Args:
            query: 查询关键词
            experience_type: 经验类型过滤
            agents: Agent过滤
            tags: 标签过滤
            min_confidence: 最小置信度
            min_success_rate: 最小成功率
            limit: 返回数量限制

        Returns:
            List[Experience]: 匹配的经验列表
        """
        results = []

        for exp in self.experiences.values():
            # 类型过滤
            if experience_type and exp.experience_type != experience_type:
                continue

            # Agent过滤
            if agents and not any(agent in exp.agents_involved for agent in agents):
                continue

            # 标签过滤
            if tags and not any(tag in exp.tags for tag in tags):
                continue

            # 置信度过滤
            if exp.confidence < min_confidence:
                continue

            # 成功率过滤
            if exp.success_rate < min_success_rate:
                continue

            # 关键词过滤
            if query:
                if query.lower() not in exp.title.lower() and \
                   query.lower() not in exp.description.lower():
                    continue

            results.append(exp)

        # 按置信度和成功率排序
        results.sort(
            key=lambda e: (e.confidence, e.success_rate, e.applied_count),
            reverse=True
        )

        return results[:limit]

    def get_best_practices(self, agent: str = None, limit: int = 5) -> List[Experience]:
        """
        获取最佳实践

        Args:
            agent: Agent过滤
            limit: 返回数量

        Returns:
            List[Experience]: 最佳实践列表
        """
        return self.search_experiences(
            experience_type=ExperienceType.BEST_PRACTICE,
            agents=[agent] if agent else None,
            min_confidence=0.7,
            limit=limit
        )

    def get_anti_patterns(self, agent: str = None, limit: int = 5) -> List[Experience]:
        """
        获取反模式（应该避免的做法）

        Args:
            agent: Agent过滤
            limit: 返回数量

        Returns:
            List[Experience]: 反模式列表
        """
        return self.search_experiences(
            experience_type=ExperienceType.ANTI_PATTERN,
            agents=[agent] if agent else None,
            limit=limit
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total': len(self.experiences),
            'by_type': {},
            'total_applied': sum(e.applied_count for e in self.experiences.values()),
            'avg_success_rate': 0.0
        }

        for exp in self.experiences.values():
            type_key = exp.experience_type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1

        if self.experiences:
            stats['avg_success_rate'] = sum(
                e.success_rate for e in self.experiences.values()
            ) / len(self.experiences)

        return stats

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        experience_type: ExperienceType = None,
        min_confidence: float = 0.0
    ) -> List[Experience]:
        """
        语义搜索经验（基于向量相似度）

        Args:
            query: 查询文本
            limit: 返回数量
            experience_type: 经验类型过滤
            min_confidence: 最小置信度

        Returns:
            List[Experience]: 相似经验列表
        """
        try:
            from .vector_search import get_semantic_experience_search

            vector_search = get_semantic_experience_search()

            # 执行语义搜索
            results = vector_search.search_similar(
                query=query,
                limit=limit,
                experience_type=experience_type.value if experience_type else None,
                min_confidence=min_confidence
            )

            # 转换为Experience对象
            experiences = []
            for result in results:
                exp_id = result['experience_id']
                if exp_id in self.experiences:
                    experiences.append(self.experiences[exp_id])

            return experiences

        except ImportError:
            # 向量搜索不可用，回退到关键词搜索
            return self.search_experiences(
                query=query,
                experience_type=experience_type,
                min_confidence=min_confidence,
                limit=limit
            )

    def save_to_file(self, filepath: str):
        """保存到文件"""
        data = {
            'experiences': [e.to_dict() for e in self.experiences.values()]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'ExperienceKnowledgeBase':
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        kb = cls()
        for exp_data in data['experiences']:
            exp = Experience.from_dict(exp_data)
            kb.experiences[exp.experience_id] = exp

        return kb


class RetrospectiveSystem:
    """
    经验回溯系统

    管理任务复盘和经验提取的完整流程。
    """

    def __init__(self):
        self.knowledge_base = ExperienceKnowledgeBase()

    def retrospect_task(
        self,
        task_id: str,
        task_title: str,
        events: List[Dict[str, Any]],
        artifacts: List[Dict[str, Any]],
        iteration_count: Dict[str, int],
        success: bool,
        duration: float = 0.0
    ) -> List[Experience]:
        """
        对任务进行复盘

        Args:
            task_id: 任务ID
            task_title: 任务标题
            events: 事件列表
            artifacts: 产物列表
            iteration_count: 迭代次数统计
            success: 是否成功
            duration: 执行时长

        Returns:
            List[Experience]: 提取的经验列表
        """
        # 创建复盘对象
        retro = TaskRetrospective(task_id, task_title)

        for event in events:
            retro.add_event(event)

        for artifact in artifacts:
            retro.add_artifact(artifact)

        retro.iteration_count = iteration_count
        retro.success = success
        retro.duration = duration

        # 分析并提取经验
        experiences = retro.analyze()

        # 添加到知识库
        for exp in experiences:
            self.knowledge_base.add_experience(exp)

        return experiences

    def get_relevant_experiences(
        self,
        task_description: str,
        agent_name: str = None,
        limit: int = 5
    ) -> List[Experience]:
        """
        获取相关经验（用于任务开始前）

        Args:
            task_description: 任务描述
            agent_name: Agent名称
            limit: 返回数量

        Returns:
            List[Experience]: 相关经验列表
        """
        # 简单的关键词匹配
        # 实际应用中可以使用更复杂的语义匹配
        keywords = task_description.lower().split()

        all_experiences = []

        # 搜索成功经验
        for keyword in keywords[:3]:  # 只用前3个关键词
            exps = self.knowledge_base.search_experiences(
                query=keyword,
                experience_type=ExperienceType.SUCCESS,
                agents=[agent_name] if agent_name else None,
                min_confidence=0.6,
                limit=2
            )
            all_experiences.extend(exps)

        # 搜索最佳实践
        best_practices = self.knowledge_base.get_best_practices(
            agent=agent_name,
            limit=2
        )
        all_experiences.extend(best_practices)

        # 去重并排序
        unique_exps = {exp.experience_id: exp for exp in all_experiences}
        sorted_exps = sorted(
            unique_exps.values(),
            key=lambda e: (e.confidence, e.success_rate),
            reverse=True
        )

        return sorted_exps[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.knowledge_base.get_statistics()


# 全局回溯系统实例
_global_retrospective_system = RetrospectiveSystem()


def get_retrospective_system() -> RetrospectiveSystem:
    """获取全局回溯系统"""
    return _global_retrospective_system
