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

    def write_html(self, rows, path):
        cells = []
        for r in range(self.n):
            for c, queen_row in enumerate(rows):
                square = 'dark' if (r + c) % 2 else 'light'
                queen = '&#9819;' if queen_row == r else ''
                cells.append(f'<td class="{square}">{queen}</td>')
        table_rows = '\n'.join(
            '<tr>' + ''.join(cells[i:i+self.n]) + '</tr>'
            for i in range(0, len(cells), self.n)
        )
        path.write_text(f"""<!doctype html>
<html lang="vi">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bàn cờ {self.n} quân hậu</title>
<style>
body {{ margin: 0; background: #f3eee4; color: #202b24; font: 16px system-ui; }}
main {{ width: min(90vw, 560px); margin: 5vh auto; }}
h1 {{ font-size: clamp(22px, 5vw, 36px); }}
.frame {{ overflow: auto; border: 6px solid #293d32; border-radius: 8px; }}
table {{ width: 100%; min-width: {self.n * 22}px; border-collapse: collapse; table-layout: fixed; }}
td {{ padding: 0; height: clamp(22px, {90/self.n:.3f}vw, {560/self.n:.3f}px);
      text-align: center; font: clamp(16px, {60/self.n:.3f}vw, {420/self.n:.3f}px)/1 "Segoe UI Symbol", serif; }}
.light {{ background: #f2dcad; color: #202b24; }}
.dark {{ background: #587360; color: #fff9e8; }}
</style>
<main>
<h1>Bàn cờ {self.n} quân hậu</h1>
<div class="frame"><table aria-label="Nghiệm {self.n} quân hậu">
{table_rows}
</table></div>
</main>
</html>
""", encoding='utf-8')
