"""Windows desktop demo for placing K nonattacking queens."""
import tkinter as tk
from tkinter import ttk


MAX_SIZE = 16


def place_queens(height, width, count):
    """Return a list of (row, column) positions, or None if impossible."""
    if count > min(height, width):
        return None
    positions = []
    columns, descending, ascending = set(), set(), set()

    def search(row, remaining):
        if remaining == 0:
            return True
        if remaining > height - row:
            return False
        for col in range(width):
            diff, total = row - col, row + col
            if col in columns or diff in descending or total in ascending:
                continue
            positions.append((row, col))
            columns.add(col)
            descending.add(diff)
            ascending.add(total)
            if search(row + 1, remaining - 1):
                return True
            positions.pop()
            columns.remove(col)
            descending.remove(diff)
            ascending.remove(total)
        return search(row + 1, remaining)

    return positions if search(0, count) else None


class QueenApp:
    def __init__(self, window):
        window.title("Bàn cờ quân hậu")
        window.geometry("720x710")
        window.minsize(500, 490)
        panel = ttk.Frame(window, padding=16)
        panel.pack(fill="both", expand=True)
        self.entries = []
        for index, (label, default) in enumerate(
            (("Số hàng", "8"), ("Số cột", "8"), ("Số quân hậu", "7"))
        ):
            ttk.Label(panel, text=label).grid(row=0, column=index, sticky="w")
            entry = ttk.Entry(panel, width=11)
            entry.insert(0, default)
            entry.grid(row=1, column=index, sticky="w", padx=(0, 12))
            self.entries.append(entry)
        ttk.Button(panel, text="Giải và vẽ bàn cờ", command=self.solve).grid(
            row=1, column=3, sticky="w"
        )
        self.status = tk.StringVar()
        ttk.Label(panel, textvariable=self.status, wraplength=450).grid(
            row=2, column=0, columnspan=4, sticky="w", pady=10
        )
        self.canvas = tk.Canvas(panel, background="#f7f5ef", highlightthickness=0)
        self.canvas.grid(row=3, column=0, columnspan=4, sticky="nsew")
        panel.columnconfigure(3, weight=1)
        panel.rowconfigure(3, weight=1)
        self.board = None
        self.canvas.bind("<Configure>", self.draw)
        window.bind("<Return>", lambda event: self.solve())
        self.solve()

    def solve(self):
        try:
            height, width, count = (int(entry.get()) for entry in self.entries)
        except ValueError:
            self.status.set("Nhập số nguyên vào cả ba ô.")
            return
        if not (1 <= height <= MAX_SIZE and 1 <= width <= MAX_SIZE and count >= 0):
            self.status.set(f"Số hàng và cột phải từ 1 đến {MAX_SIZE}. Số hậu phải từ 0 trở lên.")
            return
        positions = place_queens(height, width, count)
        self.board = height, width, positions
        if positions is None:
            self.status.set(f"Vô nghiệm với {count} hậu trên bàn {height} × {width}.")
        else:
            self.status.set(f"{height} × {width} · {count} quân hậu · Nghiệm hợp lệ")
        self.draw()

    def draw(self, event=None):
        self.canvas.delete("all")
        if self.board is None:
            return
        height, width, positions = self.board
        area_w, area_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        size = min((area_w - 44) / width, (area_h - 44) / height)
        if size <= 0:
            return
        left, top = (area_w - width * size) / 2, (area_h - height * size) / 2
        occupied = set(positions or ())
        for row in range(height):
            y = top + row * size
            self.canvas.create_text(left - 10, y + size / 2, text=str(row + 1))
            for col in range(width):
                x = left + col * size
                dark = (row + col) % 2
                self.canvas.create_rectangle(
                    x, y, x + size, y + size,
                    fill="#567363" if dark else "#ecd8af", width=0,
                )
                if row == 0:
                    self.canvas.create_text(x + size / 2, top - 10, text=str(col + 1))
                if (row, col) in occupied:
                    self.canvas.create_text(
                        x + size / 2, y + size / 2, text="♛",
                        font=("Segoe UI Symbol", max(8, int(size * 0.48))),
                        fill="#fff7df" if dark else "#17281f",
                    )


if __name__ == "__main__":
    app_window = tk.Tk()
    QueenApp(app_window)
    app_window.mainloop()
