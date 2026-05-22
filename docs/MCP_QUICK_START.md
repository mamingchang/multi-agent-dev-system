# MCP工具系统 - 快速开始指南

## 🚀 立即试用

### 1. 运行演示脚本

```bash
cd /home/mamingchang/multi-agent-dev-system
python3 scripts/demo_mcp_system.py
```

**演示内容：**
- ✅ 启动MCP服务器（filesystem）
- ✅ 列出14个可用工具
- ✅ 读取文件（README.md）
- ✅ 列出目录（src/）
- ✅ 搜索文件（*.py）
- ✅ 显示Agent集成示例

### 2. 可用的MCP工具

**filesystem服务器提供14个工具：**

| 工具名称 | 功能 |
|---------|------|
| `mcp__filesystem__read_file` | 读取文件内容 |
| `mcp__filesystem__write_file` | 写入文件 |
| `mcp__filesystem__edit_file` | 编辑文件（行级别） |
| `mcp__filesystem__create_directory` | 创建目录 |
| `mcp__filesystem__list_directory` | 列出目录内容 |
| `mcp__filesystem__move_file` | 移动/重命名文件 |
| `mcp__filesystem__search_files` | 搜索文件 |
| `mcp__filesystem__get_file_info` | 获取文件信息 |
| `mcp__filesystem__directory_tree` | 目录树视图 |
| ... | 更多工具 |

### 3. 在Python中使用

```python
from src.mcp.mcp_server_manager import MCPServerManager
from src.mcp.mcp_tool_wrapper import create_mcp_tools

# 启动MCP系统
manager = MCPServerManager()
manager.start_all_servers()

# 获取工具
mcp_tools = create_mcp_tools(manager)

# 使用工具：读取文件
read_tool = mcp_tools['mcp__filesystem__read_file']
result = read_tool.execute(path='README.md')

if result.success:
    print(f"文件内容: {result.output}")
else:
    print(f"错误: {result.error}")

# 使用工具：搜索文件
search_tool = mcp_tools['mcp__filesystem__search_files']
result = search_tool.execute(path='src', pattern='*.py', recursive=True)

if result.success:
    print(f"找到的文件:\n{result.output}")

# 关闭
manager.shutdown_all_servers()
```

### 4. 在Agent中使用

**配置Agent使用MCP工具：**

```python
from src.agents.generic_agent import GenericAgent

agent_config = {
    'name': 'file_agent',
    'role': '文件处理专家',
    'tools': {
        'inherit_global': True,
        'whitelist': [
            'mcp__filesystem__read_file',
            'mcp__filesystem__write_file',
            'mcp__filesystem__search_files'
        ]
    }
}

agent = GenericAgent(name='file_agent', config=agent_config)

# Agent的tool_registry自动包含MCP工具
# LLM可以在输出中调用这些工具
```

**LLM调用示例：**

```json
{
  "analysis": "需要读取项目配置文件",
  "tool_calls": [
    {
      "tool": "mcp__filesystem__read_file",
      "parameters": {
        "path": "config/settings.json"
      }
    }
  ],
  "output": "正在读取配置..."
}
```

## 📝 配置MCP服务器

### 配置文件位置

```
config/mcp/global_servers.json
```

### 启用/禁用服务器

```json
{
  "servers": {
    "filesystem": {
      "enabled": true,    // 改为false禁用
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    }
  }
}
```

### 添加新的MCP服务器

**本地stdio服务器：**

```json
{
  "my_server": {
    "enabled": true,
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-xxx"]
  }
}
```

**远程HTTP服务器：**

```json
{
  "github": {
    "enabled": true,
    "transport": "http",
    "url": "https://api.github.com/mcp",
    "auth": {
      "type": "bearer",
      "token": "YOUR_GITHUB_TOKEN"
    }
  }
}
```

## 🔧 常见操作

### 查看服务器状态

```python
manager = MCPServerManager()
manager.start_all_servers()

status = manager.get_server_status()
for server, info in status.items():
    print(f"{server}: {info['tool_count']} 工具")
```

### 直接调用MCP工具

```python
# 方式1: 通过工具对象
tool = mcp_tools['mcp__filesystem__read_file']
result = tool.execute(path='file.txt')

# 方式2: 通过管理器
result = manager.call_tool(
    'filesystem',           # 服务器名
    'read_file',           # 工具名
    {'path': 'file.txt'}   # 参数
)
```

### 列出所有工具

```python
all_tools = manager.get_all_tools()

for server_name, tools in all_tools.items():
    print(f"\n{server_name}:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
```

## ⚠️ 注意事项

### 1. 服务器启动失败

如果某个服务器启动失败（如git服务器超时），系统会：
- 输出WARNING日志
- 跳过该服务器
- 继续启动其他服务器
- **不影响整体系统运行**

### 2. 工具权限

所有filesystem工具都标记为"危险"（⚠️），因为它们可以修改文件系统。在生产环境中应该：
- 配置适当的工具白名单
- 限制文件访问路径
- 启用权限检查

### 3. 远程服务器

远程HTTP服务器（github、slack等）需要：
- 配置认证信息（token/API key）
- 确保网络连接
- 处理API限流

## 📚 更多资源

- [MCP系统完整文档](MCP_COMPLETE_SUMMARY.md)
- [第一阶段实现](MCP_SYSTEM_IMPLEMENTATION.md)
- [第二阶段实现](MCP_PHASE2_COMPLETE.md)

## 🎯 下一步

1. **试用演示脚本**
   ```bash
   python3 scripts/demo_mcp_system.py
   ```

2. **在自己的代码中使用**
   - 参考上面的Python示例
   - 集成到Agent配置

3. **添加更多MCP服务器**
   - 编辑 `config/mcp/global_servers.json`
   - 重启系统

4. **探索更多工具**
   - 查看 https://github.com/modelcontextprotocol/servers
   - 安装社区MCP服务器

## ✅ 系统已就绪

- ✅ MCP系统已完整实现
- ✅ 支持3种传输协议（stdio/SSE/HTTP）
- ✅ 支持3种认证方式
- ✅ 14个filesystem工具可用
- ✅ 完整测试验证
- ✅ 可以立即使用

**开始使用吧！** 🚀
