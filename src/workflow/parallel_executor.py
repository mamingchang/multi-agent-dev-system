"""
工作流并行执行器

提供并行执行工作流节点的功能
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime


class ParallelExecutor:
    """并行执行器"""

    def __init__(self, db_session, max_concurrent: int = 5):
        self.db_session = db_session
        self.max_concurrent = max_concurrent

    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        并行执行多个任务

        Args:
            tasks: 任务列表，每个任务包含 {id, agent, task, params}
            context: 共享上下文

        Returns:
            执行结果列表
        """
        if not tasks:
            return []

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_with_semaphore(task):
            async with semaphore:
                return await self._execute_single_task(task, context)

        # 并行执行所有任务
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'task_id': tasks[i].get('id'),
                    'status': 'failed',
                    'error': str(result),
                    'completed_at': datetime.now().isoformat()
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_single_task(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行单个任务"""
        task_id = task.get('id')
        agent_type = task.get('agent')
        task_description = task.get('task')
        params = task.get('params', {})

        start_time = datetime.now()

        try:
            # 这里应该调用实际的Agent执行逻辑
            # 为了演示，我们模拟执行
            await asyncio.sleep(0.1)  # 模拟执行时间

            result = {
                'task_id': task_id,
                'agent': agent_type,
                'status': 'completed',
                'output': f"Task {task_id} completed by {agent_type}",
                'started_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat()
            }

            return result

        except Exception as e:
            return {
                'task_id': task_id,
                'agent': agent_type,
                'status': 'failed',
                'error': str(e),
                'started_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat()
            }

    async def execute_batch(
        self,
        batches: List[List[Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        批量执行任务，每批内部并行，批次之间串行

        Args:
            batches: 批次列表，每批包含多个任务
            context: 共享上下文

        Returns:
            每批的执行结果
        """
        all_results = []

        for batch in batches:
            batch_results = await self.execute_parallel(batch, context)
            all_results.append(batch_results)

            # 更新上下文（如果需要）
            if context is not None:
                context['last_batch_results'] = batch_results

        return all_results


__all__ = ['ParallelExecutor']
