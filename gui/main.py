import sys
import os
import random
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'quarto'))

import quarto
from RandomPlayer import RandomPlayer
from GA_Player import GA_Player
from GA_MinMaxPlayer import GA_MinMaxPlayer
from MinMax_Player import MinMax


# ---------------------------------------------------------------------------
# Wrapper: MinMax lacks choose_piece(), so we add random selection
# ---------------------------------------------------------------------------
class MinMaxFullPlayer(quarto.Player):
    def __init__(self, game: quarto.Quarto, depth: int = 2):
        super().__init__(game)
        self._depth = depth
        self._minmax = MinMax(game)

    def choose_piece(self) -> int:
        board = self.get_game().get_board_status()
        available = [i for i in range(16) if i not in board]
        return random.choice(available)

    def place_piece(self) -> tuple:
        result = self._minmax.place_piece(self._depth)
        if result is None:
            board = self.get_game().get_board_status()
            for y in range(4):
                for x in range(4):
                    if board[y, x] == -1:
                        return x, y
        return result


# ---------------------------------------------------------------------------
# Constants & colours
# ---------------------------------------------------------------------------
WIN_W, WIN_H = 900, 620

C_BG        = (30,  30,  40)
C_BOARD_BG  = (50,  50,  65)
C_CELL_EMPTY= (70,  70,  90)
C_CELL_HOVER= (100, 100, 130)
C_PIECE_BG  = (55,  55,  70)
C_USED      = (45,  45,  55)
C_SELECT_HL = (230, 200,  50)
C_RED       = (210,  60,  60)
C_WHITE     = (230, 230, 230)
C_GRAY      = (150, 150, 165)
C_TEXT      = (220, 220, 230)
C_BTN       = (80,  100, 160)
C_BTN_HO    = (110, 130, 200)
C_BTN_TXT   = (240, 240, 255)
C_STATUS_BG = (40,  40,  55)
C_INFO_BG   = (35,  35,  48)

BOARD_X, BOARD_Y = 20, 60
CELL_SIZE = 105
BOARD_SIZE = CELL_SIZE * 4          # 420

PANEL_X = BOARD_X + BOARD_SIZE + 20
PANEL_Y = BOARD_Y
PCELL    = 100                      # piece cell size in right panel

STATUS_H = 50
INFO_H   = 50

# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------
MENU_AI    = "MENU_AI"
MENU_ORDER = "MENU_ORDER"
GAME       = "GAME"
GAME_OVER  = "GAME_OVER"

PHASE_CHOOSE = "CHOOSE"
PHASE_PLACE  = "PLACE"


# ---------------------------------------------------------------------------
# Draw a piece as a small pictogram
# ---------------------------------------------------------------------------
def draw_piece(surface, piece: quarto.Piece, cx: int, cy: int,
               size: int, greyed: bool = False, highlight: bool = False):
    """Draw a Quarto piece at (cx, cy) centre using piece attributes."""
    half = size // 2

    if highlight:
        pygame.draw.rect(surface, C_SELECT_HL,
                         (cx - half - 4, cy - half - 4, size + 8, size + 8), 3, border_radius=6)

    # Body colour
    if greyed:
        body_col = C_USED
    elif piece.COLOURED:
        body_col = C_RED
    else:
        body_col = C_WHITE

    # Height ratio: HIGH → 80 % of cell, LOW → 50 %
    h_ratio = 0.80 if piece.HIGH else 0.50
    w = int(size * 0.55)
    h = int(size * h_ratio)
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)

    if piece.SQUARE:
        if piece.SOLID:
            pygame.draw.rect(surface, body_col, rect, border_radius=4)
        else:
            pygame.draw.rect(surface, body_col, rect, width=3, border_radius=4)
    else:  # circle / ellipse
        if piece.SOLID:
            pygame.draw.ellipse(surface, body_col, rect)
        else:
            pygame.draw.ellipse(surface, body_col, rect, width=3)

    # Dark outline so white pieces are visible
    if not greyed:
        outline_col = (60, 60, 60)
        if piece.SQUARE:
            pygame.draw.rect(surface, outline_col, rect, width=1, border_radius=4)
        else:
            pygame.draw.ellipse(surface, outline_col, rect, width=1)


# ---------------------------------------------------------------------------
# Button helper
# ---------------------------------------------------------------------------
def draw_button(surface, font, text, rect, hovered=False):
    col = C_BTN_HO if hovered else C_BTN
    pygame.draw.rect(surface, col, rect, border_radius=8)
    label = font.render(text, True, C_BTN_TXT)
    lx = rect.centerx - label.get_width() // 2
    ly = rect.centery - label.get_height() // 2
    surface.blit(label, (lx, ly))


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Quarto AI")
    clock = pygame.time.Clock()

    font_lg  = pygame.font.SysFont("segoeui", 32, bold=True)
    font_md  = pygame.font.SysFont("segoeui", 22)
    font_sm  = pygame.font.SysFont("segoeui", 17)

    # ---- game-level state (reset on new game) ----
    game     = quarto.Quarto()
    ai_player = None            # quarto.Player instance for the AI
    human_order = 0             # 0 = human plays first (player 0), 1 = second (player 1)
    state    = MENU_AI
    phase    = PHASE_CHOOSE
    current_player = 0         # 0 or 1 within the game
    selected_piece = -1        # piece chosen in CHOOSE phase
    winner   = -1
    hover_cell = None           # (col, row) on board
    hover_piece = None          # piece index in panel
    ai_choice_display = -1      # show which piece AI selected
    message  = ""

    ai_options = [
        ("Random",    lambda g: RandomPlayer(g)),
        ("GA Player", lambda g: GA_Player(g, {"alpha": 0.1, "beta": 0.2})),
        ("GA+MinMax", lambda g: GA_MinMaxPlayer(g, {"alpha": 0.1, "beta": 0.3}, depth=1)),
        ("MinMax",    lambda g: MinMaxFullPlayer(g, depth=2)),
    ]
    chosen_ai_idx = 0

    def reset_game():
        nonlocal game, ai_player, state, phase, current_player
        nonlocal selected_piece, winner, hover_cell, hover_piece
        nonlocal ai_choice_display, message

        game = quarto.Quarto()
        ai_player = ai_options[chosen_ai_idx][1](game)
        if human_order == 0:
            game.set_players((None, ai_player))   # human=0, ai=1
        else:
            game.set_players((ai_player, None))   # ai=0, human=1
        state = GAME
        phase = PHASE_CHOOSE
        current_player = 0
        selected_piece = -1
        winner = -1
        hover_cell = None
        hover_piece = None
        ai_choice_display = -1
        message = _status_msg(phase, current_player, human_order)

    def _status_msg(ph, cp, ho):
        is_human = (cp == ho)
        actor = "Your turn" if is_human else "AI thinking…"
        action = "choose a piece for your opponent" if ph == PHASE_CHOOSE else "place the piece on the board"
        return f"{actor} — {action}"

    def board_cell_at(mx, my):
        """Return (col, row) if mouse is over a board cell, else None."""
        if BOARD_X <= mx < BOARD_X + BOARD_SIZE and BOARD_Y <= my < BOARD_Y + BOARD_SIZE:
            col = (mx - BOARD_X) // CELL_SIZE
            row = (my - BOARD_Y) // CELL_SIZE
            return col, row
        return None

    def panel_piece_at(mx, my):
        """Return piece index if mouse is over a piece in the right panel, else None."""
        px_end = PANEL_X + PCELL * 4
        py_end = PANEL_Y + PCELL * 4
        if PANEL_X <= mx < px_end and PANEL_Y <= my < py_end:
            col = (mx - PANEL_X) // PCELL
            row = (my - PANEL_Y) // PCELL
            idx = row * 4 + col
            return idx
        return None

    # ------------------------------------------------------------------ draw
    def draw_menu_ai(mx, my):
        screen.fill(C_BG)
        title = font_lg.render("Quarto — Choose your opponent", True, C_TEXT)
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, 80))

        btn_w, btn_h = 260, 55
        gap = 20
        total = len(ai_options) * (btn_h + gap) - gap
        start_y = (WIN_H - total) // 2

        rects = []
        for i, (label, _) in enumerate(ai_options):
            r = pygame.Rect(WIN_W // 2 - btn_w // 2,
                            start_y + i * (btn_h + gap),
                            btn_w, btn_h)
            rects.append(r)
            draw_button(screen, font_md, label, r, r.collidepoint(mx, my))
        return rects

    def draw_menu_order(mx, my):
        screen.fill(C_BG)
        title = font_lg.render("Play first or second?", True, C_TEXT)
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, 160))
        sub = font_sm.render("(First = you choose the piece given to AI | Second = AI chooses, you place)", True, C_GRAY)
        screen.blit(sub, (WIN_W // 2 - sub.get_width() // 2, 210))

        btn_w, btn_h = 200, 55
        r1 = pygame.Rect(WIN_W // 2 - btn_w - 20, 280, btn_w, btn_h)
        r2 = pygame.Rect(WIN_W // 2 + 20, 280, btn_w, btn_h)
        draw_button(screen, font_md, "First", r1, r1.collidepoint(mx, my))
        draw_button(screen, font_md, "Second", r2, r2.collidepoint(mx, my))
        return r1, r2

    def draw_game(board_status, mx, my):
        screen.fill(C_BG)

        # ---- status bar ----
        pygame.draw.rect(screen, C_STATUS_BG, (0, 0, WIN_W, STATUS_H))
        msg_surf = font_sm.render(message, True, C_TEXT)
        screen.blit(msg_surf, (10, STATUS_H // 2 - msg_surf.get_height() // 2))

        # ---- board ----
        for row in range(4):
            for col in range(4):
                cx = BOARD_X + col * CELL_SIZE
                cy = BOARD_Y + row * CELL_SIZE
                cell_rect = pygame.Rect(cx + 3, cy + 3, CELL_SIZE - 6, CELL_SIZE - 6)

                piece_idx = board_status[row, col]
                if piece_idx >= 0:
                    pygame.draw.rect(screen, C_BOARD_BG, cell_rect, border_radius=8)
                    p = game.get_piece_charachteristics(piece_idx)
                    draw_piece(screen, p,
                               cx + CELL_SIZE // 2,
                               cy + CELL_SIZE // 2,
                               CELL_SIZE - 20)
                else:
                    hov = (hover_cell == (col, row)) and phase == PHASE_PLACE and current_player == human_order
                    col_cell = C_CELL_HOVER if hov else C_CELL_EMPTY
                    pygame.draw.rect(screen, col_cell, cell_rect, border_radius=8)

        # grid lines
        for i in range(5):
            pygame.draw.line(screen, C_BG,
                             (BOARD_X, BOARD_Y + i * CELL_SIZE),
                             (BOARD_X + BOARD_SIZE, BOARD_Y + i * CELL_SIZE), 2)
            pygame.draw.line(screen, C_BG,
                             (BOARD_X + i * CELL_SIZE, BOARD_Y),
                             (BOARD_X + i * CELL_SIZE, BOARD_Y + BOARD_SIZE), 2)

        # ---- piece panel (right) ----
        panel_label = font_sm.render("Available pieces", True, C_GRAY)
        screen.blit(panel_label, (PANEL_X, PANEL_Y - 24))

        for idx in range(16):
            row = idx // 4
            col = idx % 4
            px = PANEL_X + col * PCELL
            py = PANEL_Y + row * PCELL
            cell_rect = pygame.Rect(px + 4, py + 4, PCELL - 8, PCELL - 8)

            used = idx in board_status
            is_selected = (idx == selected_piece)
            is_ai_choice = (idx == ai_choice_display) and not is_selected

            if used:
                pygame.draw.rect(screen, C_USED, cell_rect, border_radius=6)
            else:
                is_hover = (hover_piece == idx) and phase == PHASE_CHOOSE and current_player == human_order
                bg = C_CELL_HOVER if is_hover else C_PIECE_BG
                pygame.draw.rect(screen, bg, cell_rect, border_radius=6)

            p = game.get_piece_charachteristics(idx)
            draw_piece(screen, p,
                       px + PCELL // 2,
                       py + PCELL // 2,
                       PCELL - 20,
                       greyed=used,
                       highlight=is_selected or is_ai_choice)

            if is_ai_choice:
                lbl = font_sm.render("AI→", True, C_SELECT_HL)
                screen.blit(lbl, (px + 2, py + 2))

        # ---- info bar ----
        info_y = WIN_H - INFO_H
        pygame.draw.rect(screen, C_INFO_BG, (0, info_y, WIN_W, INFO_H))
        if selected_piece >= 0:
            p = game.get_piece_charachteristics(selected_piece)
            attrs = []
            if p.HIGH:      attrs.append("High")
            else:           attrs.append("Low")
            if p.COLOURED:  attrs.append("Red")
            else:           attrs.append("White")
            if p.SOLID:     attrs.append("Solid")
            else:           attrs.append("Hollow")
            if p.SQUARE:    attrs.append("Square")
            else:           attrs.append("Circle")
            info_txt = f"Selected piece #{selected_piece}: {', '.join(attrs)}"
        else:
            info_txt = "No piece selected yet"
        info_surf = font_sm.render(info_txt, True, C_TEXT)
        screen.blit(info_surf, (10, info_y + INFO_H // 2 - info_surf.get_height() // 2))

    def draw_game_over(mx, my):
        screen.fill(C_BG)
        if winner == -1:
            txt = "It's a draw!"
        elif winner == human_order:
            txt = "You win!"
        else:
            txt = "AI wins!"
        title = font_lg.render(txt, True, C_TEXT)
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, 180))

        btn_w, btn_h = 200, 55
        r_replay = pygame.Rect(WIN_W // 2 - btn_w - 20, 300, btn_w, btn_h)
        r_menu   = pygame.Rect(WIN_W // 2 + 20, 300, btn_w, btn_h)
        draw_button(screen, font_md, "Play again", r_replay, r_replay.collidepoint(mx, my))
        draw_button(screen, font_md, "Main menu",  r_menu,   r_menu.collidepoint(mx, my))
        return r_replay, r_menu

    # ------------------------------------------------------------------ loop
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()

        # pre-draw hover state
        if state == GAME:
            board_status = game.get_board_status()
            hover_cell  = board_cell_at(mx, my)
            hover_piece = panel_piece_at(mx, my)

        # ---- event handling ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if state == MENU_AI:
                    rects = draw_menu_ai(mx, my)
                    for i, r in enumerate(rects):
                        if r.collidepoint(mx, my):
                            chosen_ai_idx = i
                            state = MENU_ORDER

                elif state == MENU_ORDER:
                    r1, r2 = draw_menu_order(mx, my)
                    if r1.collidepoint(mx, my):
                        human_order = 0
                        reset_game()
                    elif r2.collidepoint(mx, my):
                        human_order = 1
                        reset_game()

                elif state == GAME_OVER:
                    r_replay, r_menu = draw_game_over(mx, my)
                    if r_replay.collidepoint(mx, my):
                        reset_game()
                    elif r_menu.collidepoint(mx, my):
                        state = MENU_AI

                elif state == GAME:
                    is_human_turn = (current_player == human_order)

                    if phase == PHASE_CHOOSE and is_human_turn:
                        pidx = panel_piece_at(mx, my)
                        if pidx is not None and pidx not in board_status:
                            selected_piece = pidx
                            game.select(selected_piece)
                            ai_choice_display = -1
                            # Advance: next player places
                            current_player = (current_player + 1) % 2
                            phase = PHASE_PLACE
                            message = _status_msg(phase, current_player, human_order)

                    elif phase == PHASE_PLACE and is_human_turn:
                        cell = board_cell_at(mx, my)
                        if cell is not None:
                            col, row = cell
                            if board_status[row, col] == -1:
                                ok = game.place(col, row)
                                if ok:
                                    winner = game.check_winner()
                                    if winner >= 0 or game.check_finished():
                                        state = GAME_OVER
                                    else:
                                        selected_piece = -1
                                        ai_choice_display = -1
                                        # Advance: same player (who just placed) now chooses next piece
                                        phase = PHASE_CHOOSE
                                        message = _status_msg(phase, current_player, human_order)

        # ---- AI moves (non-human turns, processed outside event loop) ----
        if state == GAME:
            board_status = game.get_board_status()
            is_human_turn = (current_player == human_order)

            if not is_human_turn:
                if phase == PHASE_CHOOSE:
                    # draw once so player sees "AI thinking" message
                    draw_game(board_status, mx, my)
                    pygame.display.flip()
                    pygame.time.delay(300)

                    piece_idx = ai_player.choose_piece()
                    # Make sure piece is valid
                    while piece_idx in board_status or not game.select(piece_idx):
                        available = [i for i in range(16) if i not in board_status]
                        if not available:
                            break
                        piece_idx = random.choice(available)
                    selected_piece = piece_idx
                    ai_choice_display = piece_idx
                    game.select(piece_idx)
                    current_player = (current_player + 1) % 2
                    phase = PHASE_PLACE
                    message = _status_msg(phase, current_player, human_order)

                elif phase == PHASE_PLACE:
                    draw_game(board_status, mx, my)
                    pygame.display.flip()
                    pygame.time.delay(400)

                    x, y = ai_player.place_piece()
                    # Fallback if AI returns bad move
                    if x is None or y is None or board_status[y, x] != -1:
                        for ry in range(4):
                            for rx in range(4):
                                if board_status[ry, rx] == -1:
                                    x, y = rx, ry
                                    break
                    game.place(x, y)
                    winner = game.check_winner()
                    if winner >= 0 or game.check_finished():
                        state = GAME_OVER
                    else:
                        selected_piece = -1
                        ai_choice_display = -1
                        phase = PHASE_CHOOSE
                        message = _status_msg(phase, current_player, human_order)

        # ---- draw ----
        if state == MENU_AI:
            draw_menu_ai(mx, my)
        elif state == MENU_ORDER:
            draw_menu_order(mx, my)
        elif state == GAME:
            board_status = game.get_board_status()
            draw_game(board_status, mx, my)
        elif state == GAME_OVER:
            draw_game_over(mx, my)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
