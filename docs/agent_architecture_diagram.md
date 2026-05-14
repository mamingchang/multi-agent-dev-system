# Agent模块架构图

## 1. 整体架构分层图

```mermaid
graph TB
    subgraph "前端层"
        UI[React UI]
        WS_Client[WebSocket Client]
    end
    
    subgraph "API层"
        API[FastAPI Routes]
        WS_Server[WebSocket Server]
    end
    
    subgraph "编排层"
        Orchestrator[MessageDrivenOrchestrator]
        Queue[AsyncIO Queue]
    end
    
    subgraph "Agent层"
        BaseAgent[BaseAgent 抽象基类]
        DynamicAgent1[RequirementAnalyst]
        DynamicAgent2[Architect]
        DynamicAgent3[Developer]
        DynamicAgent4[CodeReviewer]
        DynamicAgent5[Tester]
        
        BaseAgent --> DynamicAgent1
        BaseAgent --> DynamicAgent2
        BaseAgent --> DynamicAgent3
        BaseAgent --> DynamicAgent4
        BaseAgent --> DynamicAgent5
    end
    
    subgraph "支撑层"
        LLM[LLM Client]
        Memory[Memory System]
        Task[Task & Conversation]
        DB[(Database)]
    end
    
    UI --> API
    UI <--> WS_Client
    WS_Client <--> WS_Server
    API --> Orchestrator
    WS_Server --> Orchestrator
    Orchestrator --> Queue
    Queue --> DynamicAgent1
    Queue --> DynamicAgent2
    Queue --> DynamicAgent3
    Queue --> DynamicAgent4
    Queue --> DynamicAgent5
    
    DynamicAgent1 --> LLM
    DynamicAgent1 --> Memory
    DynamicAgent1 --> Task
    
    DynamicAgent3 --> LLM
    DynamicAgent3 --> Memory
    DynamicAgent3 --> Task
    
    Orchestrator --> DB
    Task --> DB
    Memory --> DB
    
    style UI fill:#e1f5ff
    style API fill:#fff4e1
    style Orchestrator fill:#ffe1f5
    style BaseAgent fill:#e1ffe1
    style LLM fill:#f5e1ff
```

## 2. 消息驱动工作流

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端
    participant API as API层
    participant Orch as Orchestrator
    participant Queue as 消息队列
    participant Agent as Agent
    participant LLM as LLM Client
    participant DB as 数据库
    participant WS as WebSocket
    
    User->>Frontend: 输入 "@Developer 实现登录"
    Frontend->>Frontend: 解析@提及
    Frontend->>API: POST /human_message
    API->>Orch: handle_human_message()
    Orch->>Queue: 放入消息
    
    Queue->>Orch: 取出消息
    Orch->>Agent: _invoke_agent('Developer')
    Agent->>Agent: _build_system_prompt()
    Agent->>Agent: _build_user_prompt()
    Agent->>LLM: _call_llm()
    LLM-->>Agent: 返回响应
    
    Agent-->>Orch: 返回结果
    Orch->>DB: 保存事件
    Orch->>WS: 推送消息
    WS-->>Frontend: 实时更新
    Frontend-->>User: 显示Agent回复
```

## 3. Agent内部结构

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +name: str
        +role: str
        +llm_client: LLMClient
        +memory_store: MemoryStore
        +process(task)* Dict
        +_build_system_prompt() str
        +_build_user_prompt(task) str
        +_call_llm(system, user) str
        +remember(content, type)
        +recall(query) List
    }
    
    class DynamicAgent {
        +task_id: str
        +db_instance: Database
        +_get_responsibilities() str
        +process(task) Dict
    }
    
    class LLMClient {
        <<interface>>
        +chat(system, user)* str
    }
    
    class ClaudeLLMClient {
        +api_key: str
        +model: str
        +chat(system, user) str
    }
    
    class OpenAILLMClient {
        +api_key: str
        +model: str
        +chat(system, user) str
    }
    
    class MockLLMClient {
        +chat(system, user) str
    }
    
    class MemoryStore {
        +agent_name: str
        +add_memory(content, type)
        +search_memories(query)
        +get_recent_memories()
    }
    
    BaseAgent <|-- DynamicAgent
    BaseAgent --> LLMClient
    BaseAgent --> MemoryStore
    LLMClient <|.. ClaudeLLMClient
    LLMClient <|.. OpenAILLMClient
    LLMClient <|.. MockLLMClient
```

## 4. Orchestrator工作流程

```mermaid
stateDiagram-v2
    [*] --> Idle: 启动
    Idle --> WaitingMessage: 等待消息
    WaitingMessage --> ProcessingMessage: 收到消息
    ProcessingMessage --> ParseMention: 解析@提及
    ParseMention --> InvokeAgent: 找到Agent
    ParseMention --> WaitingMessage: 未找到Agent
    
    InvokeAgent --> BuildPrompt: 构建提示词
    BuildPrompt --> CallLLM: 调用LLM
    CallLLM --> SaveDB: 保存到数据库
    SaveDB --> SendWebSocket: 推送WebSocket
    SendWebSocket --> CheckMention: 检查输出中的@
    
    CheckMention --> InvokeAgent: 发现@其他Agent
    CheckMention --> WaitingMessage: 无@提及
    
    WaitingMessage --> [*]: 停止
```

## 5. 数据流图

```mermaid
flowchart LR
    subgraph Input
        A[用户输入]
        B[@提及解析]
    end
    
    subgraph Processing
        C[消息队列]
        D[Agent处理]
        E[LLM调用]
    end
    
    subgraph Output
        F[数据库存储]
        G[WebSocket推送]
        H[前端显示]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> D
    D --> F
    D --> G
    F --> H
    G --> H
    
    style A fill:#e1f5ff
    style E fill:#ffe1e1
    style H fill:#e1ffe1
```

## 6. Agent协作流程

```mermaid
sequenceDiagram
    participant Human as 人工
    participant RA as RequirementAnalyst
    participant Arch as Architect
    participant Dev as Developer
    participant Rev as CodeReviewer
    
    Human->>RA: @RequirementAnalyst 分析需求
    activate RA
    RA->>RA: 分析需求
    RA->>Arch: @Architect 请设计架构
    deactivate RA
    
    activate Arch
    Arch->>Arch: 设计架构
    Arch->>Dev: @Developer 请实现
    deactivate Arch
    
    activate Dev
    Dev->>Dev: 编写代码
    Dev->>Rev: @CodeReviewer 请审查
    deactivate Dev
    
    activate Rev
    Rev->>Rev: 审查代码
    Rev->>Dev: @Developer 请修改XX问题
    deactivate Rev
    
    activate Dev
    Dev->>Dev: 修改代码
    Dev->>Rev: @CodeReviewer 已修改，请再次审查
    deactivate Dev
    
    activate Rev
    Rev->>Rev: 审查通过
    Rev->>Human: 代码已完成
    deactivate Rev
```

## 7. 记忆系统架构

```mermaid
graph TB
    subgraph "Agent"
        A[Agent实例]
    end
    
    subgraph "Memory System"
        MS[MemoryStore]
        
        subgraph "记忆类型"
            STM[短期记忆<br/>24小时]
            LTM[长期记忆<br/>永久]
            WM[工作记忆<br/>当前任务]
        end
        
        subgraph "操作"
            Add[添加记忆]
            Search[搜索记忆]
            Recall[回忆记忆]
        end
    end
    
    subgraph "Storage"
        DB[(SQLite数据库)]
    end
    
    A --> MS
    MS --> STM
    MS --> LTM
    MS --> WM
    
    MS --> Add
    MS --> Search
    MS --> Recall
    
    STM --> DB
    LTM --> DB
    WM --> DB
    
    style STM fill:#e1f5ff
    style LTM fill:#ffe1e1
    style WM fill:#e1ffe1
```

## 8. LLM适配器模式

```mermaid
classDiagram
    class BaseLLMClient {
        <<interface>>
        +chat(system, user)* str
    }
    
    class ClaudeLLMClient {
        -api_key: str
        -model: str
        -base_url: str
        +chat(system, user) str
        -_call_api() dict
    }
    
    class OpenAILLMClient {
        -api_key: str
        -model: str
        -base_url: str
        +chat(system, user) str
        -_call_api() dict
    }
    
    class OllamaLLMClient {
        -model: str
        -base_url: str
        +chat(system, user) str
        -_call_api() dict
    }
    
    class MockLLMClient {
        +chat(system, user) str
    }
    
    class LLMFactory {
        +create_llm_client(type, config) BaseLLMClient
    }
    
    BaseLLMClient <|.. ClaudeLLMClient
    BaseLLMClient <|.. OpenAILLMClient
    BaseLLMClient <|.. OllamaLLMClient
    BaseLLMClient <|.. MockLLMClient
    
    LLMFactory ..> BaseLLMClient
    LLMFactory ..> ClaudeLLMClient
    LLMFactory ..> OpenAILLMClient
    LLMFactory ..> OllamaLLMClient
    LLMFactory ..> MockLLMClient
```

## 9. 完整的请求响应流程

```mermaid
flowchart TD
    Start([用户发送消息]) --> Parse[解析@提及]
    Parse --> API[API接收请求]
    API --> Auth{权限验证}
    Auth -->|失败| Error1[返回403]
    Auth -->|成功| FindOrch{查找Orchestrator}
    
    FindOrch -->|不存在| StartOrch[启动新Orchestrator]
    FindOrch -->|已存在| UseOrch[使用现有Orchestrator]
    
    StartOrch --> Queue[放入消息队列]
    UseOrch --> Queue
    
    Queue --> Dequeue[从队列取出]
    Dequeue --> FindAgent{查找Agent}
    
    FindAgent -->|不存在| Error2[返回错误]
    FindAgent -->|存在| InvokeAgent[调用Agent]
    
    InvokeAgent --> BuildSysPrompt[构建系统提示词]
    BuildSysPrompt --> BuildUserPrompt[构建用户提示词]
    BuildUserPrompt --> CallLLM[调用LLM]
    
    CallLLM --> LLMSuccess{调用成功?}
    LLMSuccess -->|失败| Error3[返回LLM错误]
    LLMSuccess -->|成功| SaveDB[保存到数据库]
    
    SaveDB --> SendWS[推送WebSocket]
    SendWS --> CheckMention{检查@提及}
    
    CheckMention -->|有| Queue
    CheckMention -->|无| End([结束])
    
    Error1 --> End
    Error2 --> End
    Error3 --> End
    
    style Start fill:#e1f5ff
    style CallLLM fill:#ffe1e1
    style End fill:#e1ffe1
    style Error1 fill:#ffcccc
    style Error2 fill:#ffcccc
    style Error3 fill:#ffcccc
```

## 10. 部署架构

```mermaid
graph TB
    subgraph "客户端"
        Browser[浏览器]
    end
    
    subgraph "前端服务器"
        Vite[Vite Dev Server<br/>:3000]
    end
    
    subgraph "后端服务器"
        FastAPI[FastAPI<br/>:8000]
        
        subgraph "核心模块"
            API_Routes[API Routes]
            WS_Manager[WebSocket Manager]
            Orchestrator_Pool[Orchestrator Pool]
        end
        
        subgraph "Agent池"
            Agent1[Agent 1]
            Agent2[Agent 2]
            Agent3[Agent 3]
        end
    end
    
    subgraph "外部服务"
        Claude[Claude API]
        OpenAI[OpenAI API]
        Ollama[Ollama Local]
    end
    
    subgraph "数据存储"
        SQLite[(SQLite DB)]
        Files[项目文件存储]
    end
    
    Browser <--> Vite
    Vite <--> FastAPI
    
    FastAPI --> API_Routes
    FastAPI --> WS_Manager
    API_Routes --> Orchestrator_Pool
    WS_Manager --> Orchestrator_Pool
    
    Orchestrator_Pool --> Agent1
    Orchestrator_Pool --> Agent2
    Orchestrator_Pool --> Agent3
    
    Agent1 --> Claude
    Agent2 --> OpenAI
    Agent3 --> Ollama
    
    FastAPI --> SQLite
    FastAPI --> Files
    
    style Browser fill:#e1f5ff
    style FastAPI fill:#ffe1e1
    style SQLite fill:#e1ffe1
```
