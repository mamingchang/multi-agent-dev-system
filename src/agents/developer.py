"""
Developer Agent
开发者：编写代码实现功能

职责：
1. 根据架构设计编写代码
2. 实现功能需求
3. 编写单元测试
4. 遵循代码规范

改进点：
- 使用LLM生成代码
- 结构化的代码输出
- 包含测试代码
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import get_config_loader, LLMFactory, LLMClient, LLMError


class DeveloperAgent(BaseAgent):
    """开发者Agent - 负责编写代码"""

    def __init__(self, name: str = "Developer", config: Dict[str, Any] = None):
        super().__init__(name, "开发者", config)
        self.llm_client: Optional[LLMClient] = None
        self._initialize_llm()

    def _initialize_llm(self):
        """初始化LLM客户端"""
        try:
            loader = get_config_loader()
            llm_config = loader.get_agent_config(self.name)
            self.llm_client = LLMFactory.create(llm_config)
            print(f"[{self.name}] ✓ LLM客户端初始化成功")
        except Exception as e:
            print(f"[{self.name}] ⚠️  LLM客户端初始化失败: {str(e)}")
            self.llm_client = None

    def _build_system_prompt(self) -> str:
        """构建系统提示词 - 定义开发者角色"""
        return """你是专业的软件开发工程师，负责编写高质量代码。

输出JSON格式，包含：
- files: 代码文件列表，每个文件包含path和content
- tests: 测试文件列表
- documentation: 代码文档
- dependencies: 依赖包列表

注意：
1. 代码要规范、可读、有注释
2. 包含必要的错误处理
3. 遵循最佳实践
4. 代码要完整可运行"""

    def _build_user_prompt(self, task: Task) -> str:
        """构建用户提示词"""
        arch = None
        for artifact in task.artifacts:
            if artifact.get('type') == 'architecture_design':
                arch = artifact.get('content')
                break

        prompt = f"请为'{task.title}'编写代码实现。\n"
        if arch:
            tech = arch.get('technology_stack', {})
            prompt += f"技术栈：后端{tech.get('backend', {}).get('framework', 'N/A')}\n"
        return prompt

    def _develop_with_llm(self, task: Task) -> Dict[str, Any]:
        """使用LLM生成代码"""
        print(f"[{self.name}] 使用LLM生成代码...")
        response = self.llm_client.call(
            prompt=self._build_user_prompt(task),
            system_prompt=self._build_system_prompt(),
            temperature=0.3,  # 低温度，代码要准确
            max_tokens=8192   # 代码可能很长
        )
        try:
            return json.loads(response.content)
        except:
            return self._develop_basic(task)

    def _develop_basic(self, task: Task) -> Dict[str, Any]:
        """简单模式 - 生成基础代码框架"""
        return {
            "files": [
                {
                    "path": "main.py",
                    "content": "# TODO: 实现主程序\nprint('Hello World')"
                }
            ],
            "tests": [],
            "documentation": "待完善",
            "dependencies": ["fastapi", "uvicorn"]
        }

    def process(self, task: Task) -> Dict[str, Any]:
        """处理任务"""
        print(f"\n{'='*80}\n[{self.name}] 开始编写代码\n{'='*80}")
        task.update_status(TaskStatus.IN_DEVELOPMENT, self.name)

        try:
            code = self._develop_with_llm(task) if self.llm_client else self._develop_basic(task)

            print(f"[{self.name}] ✓ 代码编写完成")
            print(f"  文件数：{len(code.get('files', []))}个")

            task.add_artifact(artifact_type="code", content=code, agent=self.name)

            return {
                'success': True,
                'message': '代码编写完成',
                'next_agent': 'CodeReviewer',
                'code': code
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'next_agent': None}
