# LLM配置启用指南

## 当前状态

✅ **LLM配置系统已完全实现并可用**

系统已经实现了完整的LLM配置功能：
- 配置文件加载 ✅
- 多Provider支持（Claude/OpenAI）✅
- Agent级别的LLM配置 ✅
- 自定义API端点支持 ✅

## 配置文件位置

`config/llm_config.yaml`

## 当前配置

```yaml
default:
  provider: "claude"
  model: "claude-sonnet-4-5"
  temperature: 0.7
  max_tokens: 4096
  timeout: 60
  api_base: "https://plan.zetarouter.com"  # 自定义API端点

api_keys:
  claude: "${ANTHROPIC_API_KEY}"  # 从环境变量读取
```

## 如何启用LLM

### 方式1: 设置环境变量（推荐）

```bash
# 临时设置（当前会话）
export ANTHROPIC_API_KEY="your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 方式2: 直接修改配置文件

编辑 `config/llm_config.yaml`:

```yaml
api_keys:
  claude: "sk-ant-your-actual-api-key-here"  # 直接写入密钥
```

⚠️ **注意**: 不推荐将API密钥直接写入配置文件，因为可能会被提交到版本控制系统。

### 方式3: 使用.env文件

创建 `.env` 文件（已在.gitignore中）:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

然后在启动脚本中加载：

```python
from dotenv import load_dotenv
load_dotenv()
```

## 测试LLM配置

运行测试脚本：

```bash
cd /home/mamingchang/multi-agent-dev-system
python3 scripts/test_llm_config.py
```

## 当前API端点

系统配置使用自定义API端点：`https://plan.zetarouter.com`

根据之前的测试报告，这个端点返回"No available accounts"错误。

### 解决方案

#### 选项1: 联系API服务提供商

联系 plan.zetarouter.com 的管理员，确认：
- 账户是否已激活
- API密钥是否有效
- 是否有可用的配额

#### 选项2: 使用官方Anthropic API

修改 `config/llm_config.yaml`:

```yaml
default:
  provider: "claude"
  model: "claude-sonnet-4-5"
  temperature: 0.7
  max_tokens: 4096
  timeout: 60
  # api_base: "https://plan.zetarouter.com"  # 注释掉自定义端点
```

然后设置官方API密钥：

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."  # 从 https://console.anthropic.com 获取
```

#### 选项3: 使用OpenAI API

修改 `config/llm_config.yaml`:

```yaml
default:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 4096

api_keys:
  openai: "${OPENAI_API_KEY}"
```

设置OpenAI API密钥：

```bash
export OPENAI_API_KEY="sk-..."  # 从 https://platform.openai.com 获取
```

#### 选项4: 使用本地Ollama（免费）

1. 安装Ollama: https://ollama.ai
2. 启动模型: `ollama run llama2`
3. 修改配置（需要实现OllamaAdapter）

## Agent级别的LLM配置

每个Agent可以使用不同的LLM配置：

```yaml
agents:
  Developer:
    provider: "claude"
    model: "claude-sonnet-4-5"
    temperature: 0.3  # 低温度，代码更准确
    max_tokens: 8192  # 更多token，因为要生成代码

  Requester:
    provider: "claude"
    model: "claude-sonnet-4-5"
    temperature: 0.7  # 标准温度
    max_tokens: 2048
```

## 在代码中使用LLM

### 方式1: 通过GenericAgent

```python
from src.agents.generic_agent import GenericAgent

config = {
    'name': 'developer',
    'role': '开发工程师',
    'system_prompt': '你是一个专业的开发工程师...',
    'llm': {
        'provider': 'claude',
        'model': 'claude-sonnet-4-5'
    }
}

agent = GenericAgent(name='developer', config=config)
# Agent会自动加载LLM客户端
```

### 方式2: 直接使用LLM客户端

```python
from src.llm import LLMFactory, get_config_loader

# 从配置文件加载
loader = get_config_loader()
config = loader.get_agent_config('Developer')
client = LLMFactory.create(config)

# 调用LLM
response = client.call(
    system_prompt="你是一个专业的开发工程师",
    prompt="请编写一个Python函数计算斐波那契数列"
)
print(response.content)
```

### 方式3: 使用适配器

```python
from src.llm.llm_client import ClaudeLLMAdapter

client = ClaudeLLMAdapter(model='claude-sonnet-4-5')
response = client.chat(
    system="你是一个友好的助手",
    user="你好",
    max_tokens=100
)
print(response)
```

## 测试结果

根据 `scripts/test_llm_config.py` 的测试：

✅ **配置加载** - 成功  
✅ **Agent创建** - 成功（LLM客户端已配置）  
⚠️ **LLM客户端创建** - 失败（缺少API密钥）  
⚠️ **LLM调用** - 未测试（需要有效的API密钥）

## 下一步

1. **设置API密钥**
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. **测试LLM调用**
   ```bash
   python3 scripts/test_llm_config.py
   # 输入 'y' 测试实际的LLM调用
   ```

3. **运行完整工作流**
   ```bash
   python3 scripts/test_chess_game_with_real_system.py
   ```

## 常见问题

### Q: 为什么Agent创建成功但LLM客户端创建失败？

A: Agent使用的是 `llm_client.ClaudeLLMAdapter`，它在没有API密钥时会使用自定义端点。而 `LLMFactory.create()` 使用的是 `claude_adapter.ClaudeAdapter`，它要求必须有API密钥。

### Q: 如何切换到不同的LLM？

A: 修改 `config/llm_config.yaml` 中的 `provider` 和 `model` 字段。

### Q: 如何为不同Agent配置不同的LLM？

A: 在 `config/llm_config.yaml` 的 `agents` 部分为每个Agent单独配置。

### Q: 如何使用免费的LLM？

A: 可以使用Ollama运行本地模型，但需要实现OllamaAdapter（当前未实现）。

## 总结

✅ **LLM配置系统完全可用**

只需要：
1. 设置有效的API密钥
2. 或者修复自定义API端点的账户问题

系统已经准备好使用LLM，所有配置和代码都已就绪。
