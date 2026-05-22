#!/usr/bin/env python3
"""
使用Mock Agent测试象棋游戏开发工作流

不依赖LLM API，直接模拟Agent输出，验证：
1. 项目系统正确工作
2. 文件生成到正确位置
3. 完整的端到端流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING以上
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "🚀"*30)
    print("Mock Agent测试 - 象棋游戏开发")
    print("🚀"*30)

    # 步骤1: 初始化MCP系统
    print("\n步骤1: 初始化MCP系统...")
    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    manager = MCPServerManager()
    manager.start_all_servers()
    mcp_tools = create_mcp_tools(manager)
    print(f"✓ MCP系统启动成功 ({len(mcp_tools)} 个工具)")

    # 步骤2: 获取项目信息
    print("\n步骤2: 获取项目信息...")
    from src.project_manager import ProjectManager

    user_id = 'user_test'
    proj_mgr = ProjectManager(user_id=user_id)

    if not proj_mgr.project_exists('chess_game'):
        print("✗ 项目不存在")
        return 1

    project = proj_mgr.get_project('chess_game')
    workspace_dir = proj_mgr.get_project_workspace('chess_game')
    print(f"✓ 项目: {project.project_id}")
    print(f"  工作空间: {workspace_dir}")

    # 步骤3: 直接使用MCP工具生成代码
    print("\n步骤3: 使用MCP工具生成代码...")

    # 获取工具
    write_file_tool = mcp_tools.get('mcp__filesystem__write_file')
    create_dir_tool = mcp_tools.get('mcp__filesystem__create_directory')

    if not write_file_tool or not create_dir_tool:
        print("✗ 缺少必要的MCP工具")
        return 1

    # 创建代码文件
    files_to_create = {
        'chess_board.py': '''"""象棋棋盘类"""

class Board:
    """10x9的象棋棋盘"""

    def __init__(self):
        self.grid = [[None for _ in range(9)] for _ in range(10)]
        self.init_pieces()

    def init_pieces(self):
        """初始化棋子位置"""
        pass

    def get_piece(self, row, col):
        """获取指定位置的棋子"""
        if 0 <= row < 10 and 0 <= col < 9:
            return self.grid[row][col]
        return None

    def set_piece(self, row, col, piece):
        """设置指定位置的棋子"""
        if 0 <= row < 10 and 0 <= col < 9:
            self.grid[row][col] = piece

    def display(self):
        """显示棋盘"""
        print("\\n  0 1 2 3 4 5 6 7 8")
        for i, row in enumerate(self.grid):
            print(f"{i} ", end="")
            for piece in row:
                if piece:
                    print(piece.symbol, end=" ")
                else:
                    print(".", end=" ")
            print()
''',
        'chess_piece.py': '''"""象棋棋子类"""

class Piece:
    """棋子基类"""

    def __init__(self, color, row, col):
        self.color = color  # 'red' or 'black'
        self.row = row
        self.col = col
        self.symbol = '?'

    def can_move(self, board, to_row, to_col):
        """检查是否可以移动到目标位置"""
        return False


class King(Piece):
    """将/帅"""

    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '帅' if color == 'red' else '将'


class Rook(Piece):
    """车"""

    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '车'


class Pawn(Piece):
    """兵/卒"""

    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '兵' if color == 'red' else '卒'
''',
        'chess_game.py': '''"""象棋游戏主逻辑"""

from chess_board import Board
from chess_piece import King, Rook, Pawn


class Game:
    """象棋游戏控制器"""

    def __init__(self):
        self.board = Board()
        self.current_player = 'red'
        self.game_over = False

    def start(self):
        """开始游戏"""
        print("欢迎来到单机象棋游戏！")
        print("这是一个简化版本的演示")

        while not self.game_over:
            self.board.display()
            print(f"\\n当前玩家: {self.current_player}")

            # 简化版：直接结束
            choice = input("\\n输入 'q' 退出游戏: ")
            if choice.lower() == 'q':
                self.game_over = True

        print("\\n游戏结束！")

    def switch_player(self):
        """切换玩家"""
        self.current_player = 'black' if self.current_player == 'red' else 'red'
''',
        'main.py': '''"""象棋游戏入口"""

from chess_game import Game


def main():
    """主函数"""
    game = Game()
    game.start()


if __name__ == '__main__':
    main()
''',
        'README.md': '''# 单机象棋游戏

## 简介

这是一个简单的单机象棋游戏演示版本。

## 功能

- 基本的棋盘显示
- 棋子类设计
- 游戏主循环

## 运行

```bash
cd users/user_test/projects/chess_game/workspace
python3 main.py
```

## 说明

这是一个简化的演示版本，展示了基本的代码结构。
完整版本需要实现：
1. 完整的走棋规则
2. 规则验证
3. AI对手
4. 胜负判断

## 文件结构

- chess_board.py - 棋盘类
- chess_piece.py - 棋子类
- chess_game.py - 游戏逻辑
- main.py - 程序入口
'''
    }

    created_files = []
    for filename, content in files_to_create.items():
        file_path = str(workspace_dir / filename)
        result = write_file_tool.execute(path=file_path, content=content)
        if result.success:
            print(f"✓ {filename}")
            created_files.append(filename)
        else:
            print(f"✗ {filename}: {result.error}")

    print(f"\n✓ 创建了 {len(created_files)} 个文件")

    # 步骤4: 验证生成的文件
    print("\n步骤4: 验证生成的文件...")
    if workspace_dir.exists():
        files = list(workspace_dir.glob('*.py'))
        md_files = list(workspace_dir.glob('*.md'))
        print(f"✓ 工作空间: {workspace_dir}")
        print(f"  Python文件: {len(files)} 个")
        for f in files:
            print(f"    - {f.name}")
        print(f"  文档文件: {len(md_files)} 个")
        for f in md_files:
            print(f"    - {f.name}")
    else:
        print(f"✗ 工作空间不存在")

    # 步骤5: 测试运行
    print("\n步骤5: 测试代码...")
    import subprocess
    try:
        # 测试导入
        result = subprocess.run(
            ['python3', '-c', 'from chess_board import Board; from chess_piece import Piece; from chess_game import Game; print("✓ 导入成功")'],
            cwd=str(workspace_dir),
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"✗ 导入失败: {result.stderr}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 清理
    print("\n正在关闭MCP系统...")
    manager.shutdown_all_servers()

    print("\n" + "="*60)
    print("✓ 测试完成！")
    print("="*60)
    print(f"\n项目位置: {workspace_dir}")
    print(f"运行方式: cd {workspace_dir} && python3 main.py")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
