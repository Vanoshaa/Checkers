import tkinter as tk
from tkinter import messagebox, filedialog
import pickle
import random
import os

SIZE = 8  # размер доски 8x8


class Checker:
    def __init__(self, is_white, row, col):
        self.is_white = is_white
        self.row = row
        self.col = col
        self.is_king = False


class GameState:
    def __init__(self, checkers, white_turn, game_ended):
        self.checkers = []
        for ch in checkers:
            copy = Checker(ch.is_white, ch.row, ch.col)
            copy.is_king = ch.is_king
            self.checkers.append(copy)
        self.white_turn = white_turn
        self.game_ended = game_ended


class CheckersGame:
    def __init__(self, master, vs_ai=False):
        self.master = master
        self.vs_ai = vs_ai

        self.master.title("Шашки")
        self.cell_size = 60
        self.canvas_size = self.cell_size * SIZE

        self.canvas = tk.Canvas(self.master, width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack()

        # Меню
        menubar = tk.Menu(self.master)
        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="Новая игра", command=self.new_game)
        game_menu.add_command(label="Сохранить", command=self.save_game)
        game_menu.add_command(label="Загрузить", command=self.load_game)
        game_menu.add_command(label="Выход", command=self.master.quit)
        menubar.add_cascade(label="Игра", menu=game_menu)
        self.master.config(menu=menubar)

        self.canvas.bind("<Button-1>", self.on_click)

        self.light_brown = "#b58863"
        self.dark_brown = "#6d4721"

        self.board = [[None] * SIZE for _ in range(SIZE)]
        self.white_turn = True
        self.selected_checker = None
        self.highlighted_moves = []
        self.game_ended = False

        self.new_game()

    def new_game(self):
        self.board = [[None] * SIZE for _ in range(SIZE)]

        # Черные в верхних рядах
        for row in range(3):
            for col in range(SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Checker(False, row, col)

        # Белые в нижних рядах
        for row in range(SIZE - 3, SIZE):
            for col in range(SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Checker(True, row, col)

        self.white_turn = True
        self.selected_checker = None
        self.highlighted_moves = []
        self.game_ended = False
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        # Рисуем доску
        for r in range(SIZE):
            for c in range(SIZE):
                color = self.light_brown if (r + c) % 2 == 0 else self.dark_brown
                self.canvas.create_rectangle(c * self.cell_size, r * self.cell_size,
                                             (c + 1) * self.cell_size, (r + 1) * self.cell_size,
                                             fill=color, outline=color)
        # Подсветка возможных ходов
        for (rr, cc) in self.highlighted_moves:
            self.canvas.create_rectangle(cc * self.cell_size, rr * self.cell_size,
                                         (cc + 1) * self.cell_size, (rr + 1) * self.cell_size,
                                         outline="yellow", width=2)

        # Рисуем шашки
        for r in range(SIZE):
            for c in range(SIZE):
                ch = self.board[r][c]
                if ch is not None:
                    color = "white" if ch.is_white else "black"
                    self.canvas.create_oval(c * self.cell_size + 5, r * self.cell_size + 5,
                                            (c + 1) * self.cell_size - 5, (r + 1) * self.cell_size - 5,
                                            fill=color, outline=color)
                    if ch.is_king:
                        self.canvas.create_text(c * self.cell_size + self.cell_size // 2,
                                                r * self.cell_size + self.cell_size // 2,
                                                text="K", fill="red", font=("Arial", 14, "bold"))

    def on_click(self, event):
        if self.game_ended:
            return

        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if not self.is_valid_cell(row, col):
            return

        if self.selected_checker is None:
            # Выбор шашки
            ch = self.board[row][col]
            if ch and ch.is_white == self.white_turn:
                self.selected_checker = ch
                self.highlighted_moves = self.get_possible_moves(ch)
        else:
            # Выбрана шашка, проверяем клик по подсвеченному ходу
            if (row, col) in self.highlighted_moves:
                self.make_move(self.selected_checker, row, col)
            else:
                # Перевыбор шашки
                ch = self.board[row][col]
                if ch and ch.is_white == self.white_turn:
                    self.selected_checker = ch
                    self.highlighted_moves = self.get_possible_moves(ch)
                else:
                    self.selected_checker = None
                    self.highlighted_moves = []

        self.draw_board()

    def is_valid_cell(self, r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE

    def get_all_checkers(self):
        result = []
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] is not None:
                    result.append(self.board[r][c])
        return result

    def get_possible_moves(self, checker):
        moves = []
        if checker.is_king:
            move_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            capture_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        else:
            move_directions = [(-1, -1), (-1, 1)] if checker.is_white else [(1, -1), (1, 1)]
            capture_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]  # Все направления для рубок

        # Сначала проверяем рубки
        capture_moves = self.get_capture_moves(checker, capture_directions)
        if capture_moves:
            return capture_moves

        # Простые ходы
        for dr, dc in move_directions:
            if checker.is_king:
                # Дамка может двигаться по диагонали до блокировки
                nr, nc = checker.row + dr, checker.col + dc
                while self.is_valid_cell(nr, nc) and self.board[nr][nc] is None:
                    moves.append((nr, nc))
                    nr += dr
                    nc += dc
            else:
                # Обычная шашка делает ход на одну клетку
                nr = checker.row + dr
                nc = checker.col + dc
                if self.is_valid_cell(nr, nc) and self.board[nr][nc] is None:
                    moves.append((nr, nc))
        return moves

    def get_capture_moves(self, checker, directions):
        moves = []
        for dr, dc in directions:
            if checker.is_king:
                # Дамка ищет шашку противника по диагонали
                nr, nc = checker.row + dr, checker.col + dc
                while self.is_valid_cell(nr, nc) and self.board[nr][nc] is None:
                    nr += dr
                    nc += dc
                if self.is_valid_cell(nr, nc) and self.board[nr][nc].is_white != checker.is_white:
                    # Найдена шашка противника, ищем свободные клетки после неё
                    jr, jc = nr + dr, nc + dc
                    while self.is_valid_cell(jr, jc) and self.board[jr][jc] is None:
                        moves.append((jr, jc))
                        jr += dr
                        jc += dc
            else:
                # Обычная шашка ищет шашку противника на соседней клетке
                nr = checker.row + dr
                nc = checker.col + dc
                if self.is_valid_cell(nr, nc) and self.board[nr][nc] is not None:
                    if self.board[nr][nc].is_white != checker.is_white:
                        jr = nr + dr
                        jc = nc + dc
                        if self.is_valid_cell(jr, jc) and self.board[jr][jc] is None:
                            moves.append((jr, jc))
        return moves

    def make_move(self, checker, new_row, new_col):
        was_capture = False
        row_diff = new_row - checker.row
        col_diff = new_col - checker.col

        # Проверка рубки
        if checker.is_king:
            # Найти шашку, через которую произошла рубка
            dr = row_diff
            dc = col_diff
            step_r = 1 if dr > 0 else -1
            step_c = 1 if dc > 0 else -1
            current_r, current_c = checker.row + step_r, checker.col + step_c
            captured = None
            while (current_r != new_row) and (current_c != new_col):
                if self.board[current_r][current_c] is not None:
                    if self.board[current_r][current_c].is_white != checker.is_white:
                        if captured is None:
                            captured = (current_r, current_c)
                        else:
                            # Более одной шашки противника на пути, недопустимый ход
                            captured = None
                            break
                    else:
                        # Своя шашка на пути, недопустимый ход
                        captured = None
                        break
                current_r += step_r
                current_c += step_c
            if captured:
                self.board[captured[0]][captured[1]] = None
                was_capture = True
        else:
            if abs(row_diff) == 2 and abs(col_diff) == 2:
                captured_r = checker.row + row_diff // 2
                captured_c = checker.col + col_diff // 2
                self.board[captured_r][captured_c] = None
                was_capture = True

        self.board[checker.row][checker.col] = None
        checker.row = new_row
        checker.col = new_col
        self.board[new_row][new_col] = checker

        # Проверяем превращение в дамку
        if not checker.is_king:
            if (checker.is_white and new_row == 0) or (not checker.is_white and new_row == SIZE - 1):
                checker.is_king = True

        if was_capture:
            # Проверяем продолжение рубки
            dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)] if checker.is_king else (
                [(-1, -1), (-1, 1)] if checker.is_white else [(1, -1), (1, 1)])
            capture_moves = self.get_capture_moves(checker, dirs)
            if capture_moves:
                self.selected_checker = checker
                self.highlighted_moves = capture_moves
                self.draw_board()
                return

        self.white_turn = not self.white_turn
        self.selected_checker = None
        self.highlighted_moves = []

        # Проверяем конец игры
        self.check_for_game_end()
        self.draw_board()

        if self.vs_ai and not self.white_turn and not self.game_ended:
            self.master.after(500, self.make_ai_move)

    def make_ai_move(self):
        # Простой AI для чёрных
        black_checkers = [ch for ch in self.get_all_checkers() if not ch.is_white]
        movable = []
        for ch in black_checkers:
            if self.get_possible_moves(ch):
                movable.append(ch)

        if not movable:
            # Нет ходов
            self.game_ended = True
            self.show_game_end_dialog()
            return

        # Сначала пытаемся найти все шашки, которые могут сделать рубку
        capture_checkers = [ch for ch in movable if self.get_capture_moves(ch, [(1, 1), (1, -1), (-1, 1), (-1, -1)])]
        if capture_checkers:
            chosen = random.choice(capture_checkers)
        else:
            chosen = random.choice(movable)

        moves = self.get_possible_moves(chosen)
        if not moves:
            # На всякий случай, если нет возможных ходов
            self.game_ended = True
            self.show_game_end_dialog()
            return

        move = random.choice(moves)
        self.make_move(chosen, move[0], move[1])

    def check_for_game_end(self):
        if self.no_moves_available(True):
            # Белые не могут ходить
            self.game_ended = True
            self.show_game_end_dialog()
        elif self.no_moves_available(False):
            # Чёрные не могут ходить
            self.game_ended = True
            self.show_game_end_dialog()

    def no_moves_available(self, for_white):
        for ch in self.get_all_checkers():
            if ch.is_white == for_white:
                if self.get_possible_moves(ch):
                    return False
        return True

    def show_game_end_dialog(self):
        # Кто не может ходить - тот проиграл.
        # Если сейчас ход белых, значит белые не могут ходить, победили чёрные.
        # Если сейчас ход чёрных, значит чёрные не могут ходить, победили белые.
        if self.white_turn:
            # белые ходят, значит белые не могут
            message = "Чёрные победили!"
        else:
            message = "Белые победили!"

        messagebox.showinfo("Игра окончена", message)

    def save_game(self):
        filename = filedialog.asksaveasfilename(defaultextension=".chk",
                                                filetypes=[("Checkers save", "*.chk"), ("All Files", "*.*")])
        if filename:
            state = GameState(self.get_all_checkers(), self.white_turn, self.game_ended)
            with open(filename, "wb") as f:
                pickle.dump(state, f)

    def load_game(self):
        filename = filedialog.askopenfilename(defaultextension=".chk",
                                              filetypes=[("Checkers save", "*.chk"), ("All Files", "*.*")])
        if filename and os.path.exists(filename):
            with open(filename, "rb") as f:
                state = pickle.load(f)
            self.restore_game_state(state)
            self.draw_board()

    def restore_game_state(self, state):
        self.board = [[None] * SIZE for _ in range(SIZE)]
        for ch in state.checkers:
            self.board[ch.row][ch.col] = ch
        self.white_turn = state.white_turn
        self.game_ended = state.game_ended
        self.selected_checker = None
        self.highlighted_moves = []


def main():
    root = tk.Tk()
    choice = messagebox.askquestion("Режим игры", "Играть против компьютера?")
    vs_ai = True if choice == "yes" else False
    app = CheckersGame(root, vs_ai=vs_ai)
    root.mainloop()


if __name__ == "__main__":
    main()
