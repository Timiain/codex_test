import random
import tkinter as tk
from dataclasses import dataclass

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 30
BASE_TICK_MS = 500
MIN_TICK_MS = 120

SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "O": [[(1, 0), (2, 0), (1, 1), (2, 1)]],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

COLORS = {
    "I": "#00d9ff",
    "O": "#ffe100",
    "T": "#a259ff",
    "S": "#2ecc71",
    "Z": "#ff5e5e",
    "J": "#3c67ff",
    "L": "#ff9f1a",
}


@dataclass
class Piece:
    kind: str
    rotation: int = 0
    x: int = 3
    y: int = 0

    @property
    def cells(self):
        return SHAPES[self.kind][self.rotation]


class Tetris:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python 俄罗斯方块")

        self.canvas = tk.Canvas(
            root,
            width=BOARD_WIDTH * CELL_SIZE,
            height=BOARD_HEIGHT * CELL_SIZE,
            bg="#1e1e1e",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, rowspan=6)

        self.preview_canvas = tk.Canvas(
            root,
            width=6 * CELL_SIZE,
            height=5 * CELL_SIZE,
            bg="#151515",
            highlightthickness=0,
        )
        self.preview_canvas.grid(row=2, column=1, padx=12, pady=(0, 8), sticky="n")

        self.score_var = tk.StringVar(value="分数: 0")
        self.lines_var = tk.StringVar(value="消行: 0")
        self.level_var = tk.StringVar(value="等级: 1")
        self.status_var = tk.StringVar(value="方向键控制，空格硬降，P暂停，R重开")

        tk.Label(root, textvariable=self.score_var, font=("Arial", 14)).grid(
            row=0, column=1, sticky="w", padx=12, pady=(10, 2)
        )
        tk.Label(root, textvariable=self.lines_var).grid(row=1, column=1, sticky="w", padx=12)
        tk.Label(root, text="下一个:").grid(row=2, column=1, sticky="nw", padx=12)
        tk.Label(root, textvariable=self.level_var).grid(row=3, column=1, sticky="w", padx=12)
        tk.Label(root, textvariable=self.status_var, fg="#666", wraplength=180, justify="left").grid(
            row=4, column=1, sticky="nw", padx=12
        )

        self.bag = []
        self.board = [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False

        self.current = self._new_piece()
        self.next_piece = self._new_piece()

        self.root.bind("<Left>", lambda _: self.move(-1, 0))
        self.root.bind("<Right>", lambda _: self.move(1, 0))
        self.root.bind("<Down>", lambda _: self.soft_drop())
        self.root.bind("<Up>", lambda _: self.rotate())
        self.root.bind("<space>", lambda _: self.hard_drop())
        self.root.bind("r", lambda _: self.restart())
        self.root.bind("R", lambda _: self.restart())
        self.root.bind("p", lambda _: self.toggle_pause())
        self.root.bind("P", lambda _: self.toggle_pause())

        self._draw()
        self._draw_preview()
        self._tick()

    def _tick_delay(self) -> int:
        return max(MIN_TICK_MS, BASE_TICK_MS - (self.level - 1) * 35)

    def _refill_bag(self):
        self.bag = list(SHAPES.keys())
        random.shuffle(self.bag)

    def _new_piece(self) -> Piece:
        if not self.bag:
            self._refill_bag()
        return Piece(kind=self.bag.pop())

    def _piece_positions(self, piece: Piece):
        for px, py in piece.cells:
            yield piece.x + px, piece.y + py

    def _valid(self, piece: Piece) -> bool:
        for x, y in self._piece_positions(piece):
            if x < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def _game_blocked(self) -> bool:
        return self.game_over or self.paused

    def move(self, dx: int, dy: int):
        if self._game_blocked():
            return
        moved = Piece(self.current.kind, self.current.rotation, self.current.x + dx, self.current.y + dy)
        if self._valid(moved):
            self.current = moved
            self._draw()

    def rotate(self):
        if self._game_blocked():
            return
        total = len(SHAPES[self.current.kind])
        rotated = Piece(self.current.kind, (self.current.rotation + 1) % total, self.current.x, self.current.y)

        for kick in (0, -1, 1, -2, 2):
            candidate = Piece(rotated.kind, rotated.rotation, rotated.x + kick, rotated.y)
            if self._valid(candidate):
                self.current = candidate
                self._draw()
                return

    def soft_drop(self):
        if self._game_blocked():
            return
        dropped = Piece(self.current.kind, self.current.rotation, self.current.x, self.current.y + 1)
        if self._valid(dropped):
            self.current = dropped
            self._draw()
        else:
            self._lock_piece()

    def hard_drop(self):
        if self._game_blocked():
            return
        while True:
            dropped = Piece(self.current.kind, self.current.rotation, self.current.x, self.current.y + 1)
            if self._valid(dropped):
                self.current = dropped
            else:
                break
        self._lock_piece()

    def _lock_piece(self):
        for x, y in self._piece_positions(self.current):
            if y < 0:
                self._end_game()
                return
            self.board[y][x] = COLORS[self.current.kind]

        self._clear_lines()
        self.current = self.next_piece
        self.next_piece = self._new_piece()
        if not self._valid(self.current):
            self._end_game()
        self._draw()
        self._draw_preview()

    def _clear_lines(self):
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(remaining)
        for _ in range(cleared):
            remaining.insert(0, [None] * BOARD_WIDTH)
        self.board = remaining

        if not cleared:
            return

        self.lines += cleared
        self.level = self.lines // 10 + 1
        self.score += [0, 100, 300, 500, 800][cleared] * self.level

        self.score_var.set(f"分数: {self.score}")
        self.lines_var.set(f"消行: {self.lines}")
        self.level_var.set(f"等级: {self.level}")

    def _end_game(self):
        self.game_over = True
        self.status_var.set("游戏结束！按 R 重新开始")

    def toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            self.status_var.set("已暂停（按 P 继续）")
        else:
            self.status_var.set("方向键控制，空格硬降，P暂停，R重开")

    def restart(self):
        self.board = [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.bag = []
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.game_over = False

        self.score_var.set("分数: 0")
        self.lines_var.set("消行: 0")
        self.level_var.set("等级: 1")
        self.status_var.set("方向键控制，空格硬降，P暂停，R重开")

        self.current = self._new_piece()
        self.next_piece = self._new_piece()

        self._draw()
        self._draw_preview()

    def _draw_block(self, x: int, y: int, color: str):
        x0 = x * CELL_SIZE
        y0 = y * CELL_SIZE
        self.canvas.create_rectangle(x0, y0, x0 + CELL_SIZE, y0 + CELL_SIZE, fill=color, outline="#2a2a2a")

    def _draw_preview(self):
        self.preview_canvas.delete("all")
        color = COLORS[self.next_piece.kind]
        for px, py in SHAPES[self.next_piece.kind][0]:
            x0 = (px + 1) * CELL_SIZE
            y0 = (py + 1) * CELL_SIZE
            self.preview_canvas.create_rectangle(
                x0,
                y0,
                x0 + CELL_SIZE,
                y0 + CELL_SIZE,
                fill=color,
                outline="#2a2a2a",
            )

    def _draw(self):
        self.canvas.delete("all")
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self._draw_block(x, y, color)

        if not self.game_over:
            color = COLORS[self.current.kind]
            for x, y in self._piece_positions(self.current):
                if y >= 0:
                    self._draw_block(x, y, color)

        if self.paused and not self.game_over:
            self.canvas.create_text(
                BOARD_WIDTH * CELL_SIZE // 2,
                BOARD_HEIGHT * CELL_SIZE // 2,
                text="PAUSED",
                fill="#ffffff",
                font=("Arial", 24, "bold"),
            )

    def _tick(self):
        if not self.game_over and not self.paused:
            self.soft_drop()
        self.root.after(self._tick_delay(), self._tick)


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
