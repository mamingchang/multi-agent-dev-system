# Agent调用过程详解

## 完整的调用流程

```
用户请求
   ↓
创建Task对象
   ↓
初始化Agent
   ↓
设置项目上下文 (权限)
   ↓
Agent.process(task) ← 入口方法
   ↓
判断：是否启用工具 + LLM可用？
   ├─ 是 → _execute_with_tools() [工具调用循环]
   │         ↓
   │      构建system_prompt (角色定义 + 工具列表)
   │         ↓
   │      构建user_prompt (任务描述 + 前置产物)
   │         ↓
   │      【循环开始】max_iterations=10
   │         ↓
   │      调用LLM.call(system_prompt, user_prompt)
   │         ↓
   │      解析LLM响应
   │         ↓
   │      判断：是否包含工具调用？
   │      ├─ 是 → 解析工具名称和参数
   │      │       ↓
   │      │    call_tool(tool_name, **args)
   │      │       ↓
   │      │    权限检查 (ToolRegistry.execute_tool)
   │      │       ↓
   │      │    执行工具 (Tool.execute)
   │      │       ↓
   │      │    返回ToolResult
   │      │       ↓
   │      │    把结果传回LLM (作为新的user_prompt)
   │      │       ↓
   │      │    【继续循环】
   │      │
   │      └─ 否 → 任务完成，返回结果
   │
   └─ 否 → _develop_with_llm() 或 _develop_basic() [传统模式]
             ↓
          一次性生成代码
             ↓
          返回结果
```

## 核心代码详解

### 1. Agent.process() - 入口方法

```python
# src/agents/developer.py

def process(self, task: Task) -> Dict[str, Any]:
    """
    处理任务的入口方法
    
    流程：
    1. 更新任务状态
    2. 判断是否使用工具调用模式
    3. 执行任务
    4. 保存产物
    """
    print(f"\n{'='*80}\n[{self.name}] 开始编写代码\n{'='*80}")
    
    # 步骤1：更新任务状态
    task.update_status(TaskStatus.IN_DEVELOPMENT, self.name)
    
    try:
        # 步骤2：判断模式
        if self.enabled_tools and self.llm_client:
            # 工具调用模式
            print(f"[{self.name}] 使用工具调用模式")
            result = self._execute_with_tools(task, max_iterations=10)
            
            if result['success']:
                # 从LLM输出中提取代码
                code = self._extract_code_from_output(result['output'])
                
                # 步骤3：保存产物到任务
                task.add_artifact(
                    artifact_type="code",
                    content=code,
                    agent=self.name
                )
                
                return {
                    'success': True,
                    'message': '代码编写完成（使用工具）',
                    'next_agent': 'CodeReviewer',
                    'code': code,
                    'tool_iterations': result.get('iterations', 0)
                }
        else:
            # 传统模式（一次性生成）
            code = self._develop_with_llm(task) if self.llm_client else self._develop_basic(task)
            
            task.add_artifact(
                artifact_type="code",
                content=code,
                agent=self.name
            )
            
            return {
                'success': True,
                'message': '代码编写完成',
                'next_agent': 'CodeReviewer',
                'code': code
            }
            
    except Exception as e:
        return {'success': False, 'message': str(e), 'next_agent': None}
```

### 2. _execute_with_tools() - 工具调用循环

```python
# src/agents/base_agent.py

def _execute_with_tools(self, task, max_iterations: int = 10) -> Dict[str, Any]:
    """
    工具调用循环的核心逻辑
    
    这是一个多轮对话循环：
    - LLM决定调用什么工具
    - 系统执行工具
    - 把结果返回给LLM
    - LLM根据结果决定下一步
    - 循环直到任务完成
    """
    
    # 步骤1：检查LLM是否可用
    if not self.llm_client:
        return {'success': False, 'message': 'LLM客户端未初始化'}
    
    # 步骤2：构建初始提示词
    system_prompt = self._build_system_prompt()  # 角色定义
    if self.enabled_tools:
        system_prompt += self._build_tools_prompt()  # 工具列表
    
    user_prompt = self._build_user_prompt(task)  # 任务描述
    
    # 步骤3：工具调用循环
    conversation_history = []  # 对话历史
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"  [工具循环 {iteration}/{max_iterations}]")
        
        try:
            # 步骤3.1：调用LLM
            response = self.llm_client.call(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3  # 低温度，更确定性
            )
            
            response_content = response.content
            
            # 步骤3.2：解析LLM响应，检查是否包含工具调用
            tool_call = self._parse_tool_call(response_content)
            
            if tool_call:
                # 步骤3.3：执行工具
                tool_name = tool_call['tool']
                tool_args = tool_call['arguments']
                
                print(f"  🔧 调用工具: {tool_name}")
                print(f"     参数: {tool_args}")
                
                # 调用工具（带权限检查）
                tool_result = self.call_tool(tool_name, **tool_args)
                
                print(f"  {'✅' if tool_result['success'] else '❌'} 工具结果: ...")
                
                # 步骤3.4：把工具结果传回LLM
                conversation_history.append({
                    'role': 'assistant',
                    'content': response_content  # LLM的工具调用
                })
                
                conversation_history.append({
                    'role': 'user',
                    'content': f"工具执行结果:\n```\n{tool_result}\n```\n\n请继续完成任务。"
                })
                
                # 更新user_prompt为最新的工具结果
                user_prompt = conversation_history[-1]['content']
                
                # 继续循环
                
            else:
                # 步骤3.5：没有工具调用，任务完成
                print(f"  ✅ 任务完成")
                
                return {
                    'success': True,
                    'output': response_content,
                    'message': '任务完成',
                    'iterations': iteration
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'LLM调用失败: {str(e)}',
                'iterations': iteration
            }
    
    # 达到最大迭代次数
    return {
        'success': False,
        'message': f'达到最大迭代次数({max_iterations})',
        'iterations': iteration
    }
```

### 3. call_tool() - 工具调用（带权限检查）

```python
# src/agents/base_agent.py

def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    调用工具（带权限检查）
    
    流程：
    1. 检查工具系统是否初始化
    2. 检查工具是否启用
    3. 调用ToolRegistry执行工具（带权限检查）
    4. 返回结果
    """
    
    # 步骤1：检查工具系统
    if not self.tool_registry:
        return {
            'success': False,
            'error': '工具系统未初始化'
        }
    
    # 步骤2：检查工具是否启用
    if self.enabled_tools and tool_name not in self.enabled_tools:
        return {
            'success': False,
            'error': f'工具未启用: {tool_name}'
        }
    
    # 步骤3：执行工具（带权限检查）
    result = self.tool_registry.execute_tool(
        tool_name,
        project_id=self.current_project_id,  # 传入项目ID进行权限检查
        **kwargs
    )
    
    # 步骤4：返回结果
    return {
        'success': result.is_success(),
        'output': result.output,
        'error': result.error,
        'metadata': result.metadata
    }
```

### 4. ToolRegistry.execute_tool() - 权限检查和工具执行

```python
# src/tools/base.py

def execute_tool(self, name: str, project_id: Optional[str] = None, **kwargs) -> ToolResult:
    """
    执行工具（带权限检查）
    
    流程：
    1. 查找工具
    2. 权限检查
    3. 执行工具
    4. 返回结果
    """
    
    # 步骤1：查找工具
    tool = self.get_tool(name)
    if not tool:
        return ToolResult(
            status=ToolResultStatus.ERROR,
            output=None,
            error=f"工具不存在: {name}"
        )
    
    # 步骤2：权限检查
    if self.permission_manager and project_id:
        permission_check = self._check_tool_permission(tool, project_id, **kwargs)
        
        if not permission_check['allowed']:
            return ToolResult(
                status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error=permission_check['reason']
            )
    
    # 步骤3：执行工具
    return tool.execute(**kwargs)
```

### 5. _check_tool_permission() - 权限检查逻辑

```python
# src/tools/base.py

def _check_tool_permission(self, tool: Tool, project_id: str, **kwargs) -> Dict[str, Any]:
    """
    检查工具权限
    
    流程：
    1. 获取项目权限配置
    2. 检查工具所需权限
    3. 检查文件路径（如果有）
    4. 检查命令（如果有）
    """
    
    # 步骤1：获取项目权限
    project_perm = self.permission_manager.get_project_permission(project_id)
    if not project_perm:
        return {
            'allowed': False,
            'reason': f'项目不存在: {project_id}'
        }
    
    # 步骤2：检查工具所需权限
    required_perm = tool.get_required_permission()
    if not project_perm.has_permission(required_perm):
        return {
            'allowed': False,
            'reason': f'缺少权限: {required_perm}'
        }
    
    # 步骤3：检查文件路径
    if 'file_path' in kwargs:
        file_path = kwargs['file_path']
        if not project_perm.is_path_allowed(file_path):
            return {
                'allowed': False,
                'reason': f'路径不允许访问: {file_path}'
            }
    
    # 步骤4：检查命令
    if 'command' in kwargs:
        command = kwargs['command']
        if not project_perm.is_command_allowed(command):
            return {
                'allowed': False,
                'reason': f'命令不允许执行: {command}'
            }
    
    return {'allowed': True}
```

## 抽象接口的实现

### save_memory() - 保存记忆

```python
# src/agents/base_agent.py

def save_memory(self, memory_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """
    保存记忆到文件
    
    内部调用write_file工具，但提供了统一的接口和格式
    """
    import json
    from datetime import datetime
    
    # 生成文件路径（统一格式）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f".memory/{self.name}/{memory_type}_{timestamp}.json"
    
    # 调用write_file工具
    return self.call_tool(
        'write_file',
        file_path=path,
        content=json.dumps(content, indent=2, ensure_ascii=False)
    )
```

### save_work_log() - 保存工作日志

```python
# src/agents/base_agent.py

def save_work_log(self, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    保存工作日志（追加模式）
    
    使用write_file的append模式，每条日志一行JSON
    """
    import json
    from datetime import datetime, date
    
    timestamp = datetime.now().isoformat()
    today = date.today().strftime("%Y%m%d")
    path = f".logs/{self.name}/work_{today}.jsonl"
    
    log_entry = {
        'timestamp': timestamp,
        'action': action,
        'details': details
    }
    
    # 调用write_file工具（追加模式）
    return self.call_tool(
        'write_file',
        file_path=path,
        content=json.dumps(log_entry, ensure_ascii=False) + '\n',
        mode='append'  # 关键：追加模式
    )
```

### save_artifact() - 保存产物

```python
# src/agents/base_agent.py

def save_artifact(self, artifact_type: str, content: str, format: str = 'md') -> Dict[str, Any]:
    """
    保存工作产物
    
    统一的产物存储位置和命名规则
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"artifacts/{self.name}/{artifact_type}_{timestamp}.{format}"
    
    # 调用write_file工具
    return self.call_tool(
        'write_file',
        file_path=path,
        content=content
    )
```

## 关键设计点

### 1. 三层架构

```
┌─────────────────────────────────────────┐
│         抽象接口层                        │
│  save_memory(), save_artifact(), ...    │
│  (统一格式、统一位置、统一命名)           │
└─────────────────────────────────────────┘
                  ↓ 调用
┌─────────────────────────────────────────┐
│         基础工具层                        │
│  read_file, write_file, search_files    │
│  (所有Agent都有)                         │
└─────────────────────────────────────────┘
                  ↓ 调用
┌─────────────────────────────────────────┐
│         专业工具层                        │
│  edit_file, run_command                 │
│  (特定Agent专用)                         │
└─────────────────────────────────────────┘
```

### 2. 权限检查流程

```
Agent.call_tool()
    ↓
ToolRegistry.execute_tool()
    ↓
_check_tool_permission()
    ↓
检查：项目权限、工具权限、路径权限、命令权限
    ↓
Tool.execute()
```

### 3. LLM工具调用格式

LLM生成的工具调用格式：

```json
{
  "tool": "write_file",
  "arguments": {
    "file_path": "calculator.py",
    "content": "def add(a, b):\n    return a + b"
  }
}
```

系统返回给LLM的结果：

```
工具执行结果:
```
{
  'success': True,
  'output': '文件已写入: calculator.py',
  'metadata': {'file_path': 'calculator.py', 'size': 50, 'lines': 2}
}
```

请继续完成任务。
```

## 总结

完整的调用链路：

1. **用户请求** → 创建Task
2. **Task** → Agent.process()
3. **Agent.process()** → _execute_with_tools()
4. **_execute_with_tools()** → LLM.call()
5. **LLM响应** → _parse_tool_call()
6. **工具调用** → call_tool()
7. **call_tool()** → ToolRegistry.execute_tool()
8. **权限检查** → _check_tool_permission()
9. **执行工具** → Tool.execute()
10. **返回结果** → 传回LLM
11. **循环** → 直到任务完成

关键特性：
- ✅ 多轮对话循环
- ✅ 权限检查
- ✅ 三层工具架构
- ✅ 统一的抽象接口
- ✅ 灵活的工具组合
