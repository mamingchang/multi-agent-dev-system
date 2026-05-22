#!/usr/bin/env python3
"""
迁移脚本：将7个标准Agent从Python类迁移到GenericAgent配置

这个脚本会：
1. 将完整的Agent配置复制到全局Agent目录
2. 更新现有项目，使其使用新的配置
3. 备份原有的.py文件（不删除，以防需要回滚）

运行方式：
    python scripts/migrate_standard_agents.py
"""

import os
import shutil
from pathlib import Path
import yaml

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 配置路径
TEMPLATES_DIR = PROJECT_ROOT / "config" / "templates"
GLOBAL_AGENTS_DIR = PROJECT_ROOT / "data" / "agents" / "global"

# 7个标准Agent
STANDARD_AGENTS = [
    'requester',
    'product_manager',
    'architect',
    'developer',
    'code_reviewer',
    'tester',
    'devops'
]


def migrate_agent(agent_name: str):
    """
    迁移单个Agent

    Args:
        agent_name: Agent名称
    """
    # 源文件：完整配置模板
    source_file = TEMPLATES_DIR / f"{agent_name}_full.yaml"

    if not source_file.exists():
        print(f"  ⚠️  模板文件不存在: {source_file}")
        return False

    # 目标目录：全局Agent目录
    target_dir = GLOBAL_AGENTS_DIR / agent_name
    target_dir.mkdir(parents=True, exist_ok=True)

    # 目标文件
    target_config = target_dir / "config.yaml"
    target_metadata = target_dir / "metadata.json"

    # 读取模板
    with open(source_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 写入config.yaml
    with open(target_config, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    # 创建metadata.json
    metadata = {
        "agent_id": agent_name,
        "version": config.get('metadata', {}).get('version', '2.0.0'),
        "created_from": "migration_script",
        "is_standard_agent": True,
        "original_class": config.get('metadata', {}).get('original_class', f"{agent_name.title()}Agent")
    }

    import json
    with open(target_metadata, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 迁移成功: {agent_name}")
    print(f"    配置: {target_config}")
    print(f"    元数据: {target_metadata}")

    return True


def backup_python_files():
    """
    备份原有的Python文件
    """
    agents_dir = PROJECT_ROOT / "src" / "agents"
    backup_dir = PROJECT_ROOT / "backup" / "agents_py_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for agent_name in STANDARD_AGENTS:
        py_file = agents_dir / f"{agent_name}.py"
        if py_file.exists():
            backup_file = backup_dir / f"{agent_name}.py"
            shutil.copy2(py_file, backup_file)
            print(f"  ✓ 备份: {py_file} -> {backup_file}")


def main():
    """主函数"""
    print("=" * 80)
    print("🔄 开始迁移7个标准Agent到GenericAgent")
    print("=" * 80)
    print()

    # 步骤1: 备份Python文件
    print("步骤1: 备份原有的Python文件")
    print("-" * 80)
    backup_python_files()
    print()

    # 步骤2: 迁移Agent配置
    print("步骤2: 迁移Agent配置到全局目录")
    print("-" * 80)
    success_count = 0
    for agent_name in STANDARD_AGENTS:
        if migrate_agent(agent_name):
            success_count += 1
        print()

    # 步骤3: 总结
    print("=" * 80)
    print(f"✅ 迁移完成: {success_count}/{len(STANDARD_AGENTS)} 个Agent")
    print("=" * 80)
    print()

    print("接下来的步骤：")
    print("  1. 测试工作流是否正常运行")
    print("  2. 如果一切正常，可以删除原有的.py文件（已备份）")
    print("  3. 如果有问题，可以从backup目录恢复")
    print()

    print("测试命令：")
    print("  python cli/workflow.py dynamic --project <项目名> --title '测试任务' --description '测试迁移后的Agent'")
    print()


if __name__ == '__main__':
    main()
