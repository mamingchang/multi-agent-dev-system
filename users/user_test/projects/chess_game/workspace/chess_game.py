"""象棋游戏主逻辑"""

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
            print(f"\n当前玩家: {self.current_player}")

            # 简化版：直接结束
            choice = input("\n输入 'q' 退出游戏: ")
            if choice.lower() == 'q':
                self.game_over = True

        print("\n游戏结束！")

    def switch_player(self):
        """切换玩家"""
        self.current_player = 'black' if self.current_player == 'red' else 'red'
