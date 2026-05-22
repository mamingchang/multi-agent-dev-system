"""象棋棋子类"""

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
