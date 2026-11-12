"""Board representation and solver results."""
from dataclasses import dataclass


@dataclass
class Result:
    solution: list[int] | None
    seconds: float
    steps: int = 0
    attempts: int = 1


class NQueens:
    def __init__(self, n):
        if not isinstance(n, int) or n < 1:
            raise ValueError('N must be a positive integer')
        self.n = n

    def valid(self, rows):
        n = self.n
        return (rows is not None and len(rows) == n
                and all(isinstance(r, int) and 0 <= r < n for r in rows)
                and len(set(rows)) == n
                and len({r-c for c, r in enumerate(rows)}) == n
                and len({r+c for c, r in enumerate(rows)}) == n)

    def board(self, rows):
        width = max(3, len(str(self.n - 1)) + 2)
        label_width = len(str(self.n - 1))
        indent = ' ' * (label_width + 1)
        border = indent + '+' + '+'.join('-' * width for _ in rows) + '+'
        columns = ' ' + ' '.join(str(c).center(width) for c in range(self.n))
        lines = [indent + columns, border]
        for r in range(self.n):
            cells = ('Q' if queen_row == r else ' ' for queen_row in rows)
            lines.append(f'{r:>{label_width}} |' + '|'.join(cell.center(width) for cell in cells) + '|')
            lines.append(border)
        return '\n'.join(lines)
