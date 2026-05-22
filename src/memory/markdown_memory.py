"""
Markdown记忆格式支持

借鉴Claude Code的Markdown格式：
1. 使用Markdown + Frontmatter格式
2. 人类可读
3. 支持手动编辑
4. 自动生成索引文件（MEMORY.md）
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class MarkdownMemory:
    """Markdown格式的记忆管理"""

    @staticmethod
    def to_markdown(memory_data: Dict[str, Any]) -> str:
        """
        将记忆数据转换为Markdown格式

        Args:
            memory_data: 记忆数据

        Returns:
            str: Markdown格式的记忆
        """
        # 提取元数据
        name = memory_data.get('name', 'untitled')
        description = memory_data.get('description', '')
        memory_type = memory_data.get('type', 'general')
        tags = memory_data.get('tags', [])
        importance = memory_data.get('importance', 'medium')
        created_at = memory_data.get('created_at', datetime.now().isoformat())

        # 构建Frontmatter
        frontmatter = f"""---
name: {name}
description: {description}
type: {memory_type}
importance: {importance}
tags: {', '.join(tags) if tags else 'none'}
created_at: {created_at}
---

"""

        # 构建内容
        content = memory_data.get('content', '')

        # 如果content是字典，格式化输出
        if isinstance(content, dict):
            content_parts = []

            # 主要内容
            if 'content' in content:
                content_parts.append(content['content'])

            # 原因
            if 'reason' in content:
                content_parts.append(f"\n**Why:** {content['reason']}")

            # 上下文
            if 'context' in content and content['context']:
                content_parts.append(f"\n**Context:** {content['context']}")

            # 如何应用
            if 'how_to_apply' in content:
                content_parts.append(f"\n**How to apply:** {content['how_to_apply']}")

            # 其他元数据
            other_keys = set(content.keys()) - {'content', 'reason', 'context', 'how_to_apply', 'timestamp', 'category'}
            if other_keys:
                content_parts.append("\n**Additional Info:**")
                for key in other_keys:
                    content_parts.append(f"- {key}: {content[key]}")

            content = '\n'.join(content_parts)

        return frontmatter + content

    @staticmethod
    def from_markdown(markdown_text: str) -> Dict[str, Any]:
        """
        从Markdown格式解析记忆数据

        Args:
            markdown_text: Markdown文本

        Returns:
            Dict: 记忆数据
        """
        import re

        # 解析Frontmatter
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, markdown_text, re.DOTALL)

        if not match:
            # 没有Frontmatter，整个文本作为内容
            return {
                'content': markdown_text.strip()
            }

        frontmatter_text = match.group(1)
        content = match.group(2).strip()

        # 解析Frontmatter字段
        memory_data = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # 处理tags（逗号分隔）
                if key == 'tags' and value != 'none':
                    value = [tag.strip() for tag in value.split(',')]

                memory_data[key] = value

        memory_data['content'] = content

        return memory_data

    @staticmethod
    def save_to_file(memory_data: Dict[str, Any], file_path: str):
        """
        保存记忆到Markdown文件

        Args:
            memory_data: 记忆数据
            file_path: 文件路径
        """
        markdown_text = MarkdownMemory.to_markdown(memory_data)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """
        从Markdown文件加载记忆

        Args:
            file_path: 文件路径

        Returns:
            Dict: 记忆数据
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        return MarkdownMemory.from_markdown(markdown_text)


class MemoryIndex:
    """
    记忆索引管理器

    借鉴Claude Code的MEMORY.md索引文件
    """

    def __init__(self, memory_dir: str):
        """
        初始化记忆索引

        Args:
            memory_dir: 记忆目录
        """
        self.memory_dir = memory_dir
        self.index_file = os.path.join(memory_dir, 'MEMORY.md')

    def build_index(self) -> str:
        """
        构建记忆索引

        Returns:
            str: 索引内容（Markdown格式）
        """
        index_parts = [
            "# Memory Index",
            "",
            "This file contains an index of all memories for quick reference.",
            "Each memory is stored in a separate file with detailed information.",
            "",
            "---",
            ""
        ]

        # 按类型分组
        memories_by_type = self._group_memories_by_type()

        # 生成索引
        for memory_type, memories in sorted(memories_by_type.items()):
            index_parts.append(f"## {memory_type.replace('_', ' ').title()}")
            index_parts.append("")

            for memory in memories:
                name = memory.get('name', 'untitled')
                description = memory.get('description', 'No description')
                file_name = memory.get('file_name', '')

                # 格式：- [Name](file.md) — Description
                index_parts.append(f"- [{name}]({file_name}) — {description}")

            index_parts.append("")

        return '\n'.join(index_parts)

    def _group_memories_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        按类型分组记忆

        Returns:
            Dict: 按类型分组的记忆
        """
        memories_by_type = {}

        # 遍历记忆目录
        if not os.path.exists(self.memory_dir):
            return memories_by_type

        for file_name in os.listdir(self.memory_dir):
            if file_name.endswith('.md') and file_name != 'MEMORY.md':
                file_path = os.path.join(self.memory_dir, file_name)

                try:
                    # 加载记忆
                    memory_data = MarkdownMemory.load_from_file(file_path)
                    memory_data['file_name'] = file_name

                    # 按类型分组
                    memory_type = memory_data.get('type', 'general')
                    if memory_type not in memories_by_type:
                        memories_by_type[memory_type] = []

                    memories_by_type[memory_type].append(memory_data)

                except Exception as e:
                    print(f"[MemoryIndex] 加载记忆失败: {file_name} - {str(e)}")

        # 按创建时间排序
        for memory_type in memories_by_type:
            memories_by_type[memory_type].sort(
                key=lambda m: m.get('created_at', ''),
                reverse=True
            )

        return memories_by_type

    def update_index(self):
        """更新索引文件"""
        index_content = self.build_index()

        # 确保目录存在
        os.makedirs(self.memory_dir, exist_ok=True)

        # 写入索引文件
        with open(self.index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)

        print(f"[MemoryIndex] 索引已更新: {self.index_file}")

    def get_index_content(self) -> str:
        """
        获取索引内容

        Returns:
            str: 索引内容
        """
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def add_memory_to_index(self, memory_data: Dict[str, Any], file_name: str):
        """
        添加记忆到索引

        Args:
            memory_data: 记忆数据
            file_name: 文件名
        """
        # 保存为Markdown文件
        file_path = os.path.join(self.memory_dir, file_name)
        MarkdownMemory.save_to_file(memory_data, file_path)

        # 更新索引
        self.update_index()

    def remove_memory_from_index(self, file_name: str):
        """
        从索引中移除记忆

        Args:
            file_name: 文件名
        """
        file_path = os.path.join(self.memory_dir, file_name)

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[MemoryIndex] 记忆已删除: {file_name}")

        # 更新索引
        self.update_index()

    def search_memories(self, query: str = None, memory_type: str = None) -> List[Dict[str, Any]]:
        """
        搜索记忆

        Args:
            query: 搜索关键词
            memory_type: 记忆类型

        Returns:
            List[Dict]: 匹配的记忆列表
        """
        memories = []

        # 遍历记忆目录
        if not os.path.exists(self.memory_dir):
            return memories

        for file_name in os.listdir(self.memory_dir):
            if file_name.endswith('.md') and file_name != 'MEMORY.md':
                file_path = os.path.join(self.memory_dir, file_name)

                try:
                    # 加载记忆
                    memory_data = MarkdownMemory.load_from_file(file_path)
                    memory_data['file_name'] = file_name
                    memory_data['file_path'] = file_path

                    # 类型过滤
                    if memory_type and memory_data.get('type') != memory_type:
                        continue

                    # 关键词过滤
                    if query:
                        content = str(memory_data.get('content', ''))
                        name = str(memory_data.get('name', ''))
                        description = str(memory_data.get('description', ''))

                        if query.lower() not in content.lower() and \
                           query.lower() not in name.lower() and \
                           query.lower() not in description.lower():
                            continue

                    memories.append(memory_data)

                except Exception as e:
                    print(f"[MemoryIndex] 加载记忆失败: {file_name} - {str(e)}")

        return memories
