"""象棋棋盘类"""

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
        print("\n  0 1 2 3 4 5 6 7 8")
        for i, row in enumerate(self.grid):
            print(f"{i} ", end="")
            for piece in row:
                if piece:
                    print(piece.symbol, end=" ")
                else:
                    print(".", end=" ")
            print()
