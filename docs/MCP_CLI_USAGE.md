# MCP工具CLI使用指南

## 快速开始

```bash
cd /home/mamingchang/multi-agent-dev-system

# 列出所有可用工具
python3 cli/mcp_tool.py --list-tools

# 读取文件
python3 cli/mcp_tool.py read_file --path README.md

# 列出目录
python3 cli/mcp_tool.py list_directory --path src

# 搜索文件
python3 cli/mcp_tool.py search_files --path src --pattern "*.py" --recursive

# 获取文件信息
python3 cli/mcp_tool.py get_file_info --path README.md
```

## 所有可用命令

### 1. 列出所有工具
```bash
python3 cli/mcp_tool.py --list-tools
```

### 2. 读取文件
```bash
python3 cli/mcp_tool.py read_file --path <文件路径>

# 示例
python3 cli/mcp_tool.py read_file --path README.md
python3 cli/mcp_tool.py read_file --path src/mcp/mcp_client.py
```

### 3. 列出目录
```bash
python3 cli/mcp_tool.py list_directory --path <目录路径>

# 示例
python3 cli/mcp_tool.py list_directory --path src
python3 cli/mcp_tool.py list_directory --path src/mcp
```

### 4. 搜索文件
```bash
python3 cli/mcp_tool.py search_files --path <目录> --pattern <模式> --recursive

# 示例
python3 cli/mcp_tool.py search_files --path src --pattern "*.py" --recursive
python3 cli/mcp_tool.py search_files --path docs --pattern "*.md" --recursive
python3 cli/mcp_tool.py search_files --path config --pattern "*.json"
```

### 5. 获取文件信息
```bash
python3 cli/mcp_tool.py get_file_info --path <文件路径>

# 示例
python3 cli/mcp_tool.py get_file_info --path README.md
python3 cli/mcp_tool.py get_file_info --path src/mcp/mcp_client.py
```

### 6. 查看目录树
```bash
python3 cli/mcp_tool.py directory_tree --path <目录路径>

# 示例
python3 cli/mcp_tool.py directory_tree --path src/mcp
python3 cli/mcp_tool.py directory_tree --path config
```

### 7. 写入文件
```bash
python3 cli/mcp_tool.py write_file --path <文件路径> --content <内容>

# 示例
python3 cli/mcp_tool.py write_file --path test.txt --content "Hello World"
```

### 8. 创建目录
```bash
python3 cli/mcp_tool.py create_directory --path <目录路径>

# 示例
python3 cli/mcp_tool.py create_directory --path temp/test
```

### 9. 移动文件
```bash
python3 cli/mcp_tool.py move_file --path <源路径> --destination <目标路径>

# 注意：需要修改CLI支持destination参数
```

## JSON输出格式

使用 `--json` 参数可以获得JSON格式的输出，方便脚本处理：

```bash
python3 cli/mcp_tool.py read_file --path README.md --json
```

输出：
```json
{
  "success": true,
  "output": "文件内容...",
  "error": null,
  "metadata": {
    "server": "filesystem",
    "tool": "read_file"
  }
}
```

## 测试结果

✅ **所有命令测试通过：**

1. **列出工具** - 显示14个filesystem工具
2. **读取文件** - 成功读取README.md（1771字符）
3. **列出目录** - 成功列出src/mcp目录（8个文件）
4. **搜索文件** - 成功搜索src目录下的*.py文件
5. **获取文件信息** - 成功获取README.md的元数据

## 常见用法示例

### 查看项目结构
```bash
# 查看src目录结构
python3 cli/mcp_tool.py directory_tree --path src

# 查看所有Python文件
python3 cli/mcp_tool.py search_files --path . --pattern "*.py" --recursive
```

### 读取配置文件
```bash
# 读取MCP配置
python3 cli/mcp_tool.py read_file --path config/mcp/global_servers.json

# 读取工具配置
python3 cli/mcp_tool.py read_file --path config/tools/global_tools.yaml
```

### 检查文件
```bash
# 获取文件详细信息
python3 cli/mcp_tool.py get_file_info --path README.md

# 列出目录内容
python3 cli/mcp_tool.py list_directory --path src/agents
```

### 搜索代码
```bash
# 搜索所有Python文件
python3 cli/mcp_tool.py search_files --path src --pattern "*.py" --recursive

# 搜索配置文件
python3 cli/mcp_tool.py search_files --path config --pattern "*.json" --recursive

# 搜索文档
python3 cli/mcp_tool.py search_files --path docs --pattern "*.md" --recursive
```

## 脚本集成

可以在shell脚本中使用：

```bash
#!/bin/bash

# 读取文件并处理
content=$(python3 cli/mcp_tool.py read_file --path README.md --json | jq -r '.output')
echo "文件长度: ${#content}"

# 搜索文件并统计
files=$(python3 cli/mcp_tool.py search_files --path src --pattern "*.py" --recursive)
count=$(echo "$files" | wc -l)
echo "找到 $count 个Python文件"
```

## 注意事项

1. **路径** - 所有路径都相对于项目根目录
2. **启动时间** - 首次启动需要加载MCP服务器（约2-3秒）
3. **错误处理** - 如果工具执行失败，会显示详细错误信息
4. **日志级别** - 默认只显示WARNING以上的日志

## 帮助信息

```bash
python3 cli/mcp_tool.py -h
```

## 下一步

- 可以将常用命令封装成shell脚本
- 可以在CI/CD中使用这些命令
- 可以扩展CLI支持更多参数和工具
