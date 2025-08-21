import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue
import os

# --- CÁC HẰNG SỐ CẤU HÌNH ---
BOARD_WIDTH = BOARD_HEIGHT = 512
BORDER_SIZE = 25
MOVE_LOG_PANEL_WIDTH = 280
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
FLIP_BOARD = False
AI_THINK_TIME = 10 # Thời gian suy nghĩ của AI (giây)

# --- VỊ TRÍ & MÀU SẮC CÁC NÚT BẤM (ĐÃ CẬP NHẬT) ---
BUTTON_Y = BOARD_HEIGHT + 2 * BORDER_SIZE + 15
BUTTON_HEIGHT = 40
BUTTON_WIDTH = 90
BUTTON_SPACING = 15
BUTTON_PANEL_HEIGHT = BUTTON_HEIGHT + 30

# Sắp xếp lại vị trí các nút cho hợp lý
UNDO_BUTTON_RECT = p.Rect(BORDER_SIZE, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
RESET_BUTTON_RECT = p.Rect(BORDER_SIZE + BUTTON_WIDTH + BUTTON_SPACING, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
MENU_BUTTON_RECT = p.Rect(BORDER_SIZE + 2 * (BUTTON_WIDTH + BUTTON_SPACING), BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
SURRENDER_BUTTON_RECT = p.Rect(BORDER_SIZE + 3 * (BUTTON_WIDTH + BUTTON_SPACING), BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT) # Nút mới
PLAY_AGAIN_BUTTON_RECT = p.Rect(BOARD_WIDTH // 2 - 60 + BORDER_SIZE, BOARD_HEIGHT // 2 + 50, 120, 60)

# Màu sắc mới cho các nút
UNDO_COLOR = p.Color("#3b82f6") # Xanh dương
UNDO_HOVER_COLOR = p.Color("#60a5fa")
RESET_COLOR = p.Color("#ef4444") # Đỏ
RESET_HOVER_COLOR = p.Color("#f87171")
MENU_COLOR = p.Color("#22c55e") # Xanh lá
MENU_HOVER_COLOR = p.Color("#4ade80")
SURRENDER_COLOR = p.Color("#d1d5db") # Xám
SURRENDER_HOVER_COLOR = p.Color("#f9fafb")
DISABLED_COLOR = p.Color("#6b7280") # Màu khi nút bị vô hiệu hóa

# Tải ảnh quân cờ
def loadImages():
    base_path = os.path.dirname(__file__)
    image_folder = os.path.join(base_path, "images")
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        path = os.path.join(image_folder, piece + ".png")
        IMAGES[piece] = p.transform.scale(p.image.load(path), (SQUARE_SIZE, SQUARE_SIZE))

# Màn hình chọn chế độ chơi
def showMenuScreen(screen):
    global FLIP_BOARD
    screen.fill(p.Color("white"))
    title_font = p.font.SysFont("Arial", 36, True, False)
    button_font = p.font.SysFont("Arial", 20, True, False)
    buttons = [
        {"text": "Play as White", "rect": p.Rect(0, 150, 250, 60), "choice": (True, False), "flip": False},
        {"text": "Play as Black", "rect": p.Rect(0, 230, 250, 60), "choice": (False, True), "flip": True},
        {"text": "Watch AI vs AI", "rect": p.Rect(0, 310, 250, 60), "choice": (False, False), "flip": False},
        {"text": "Human vs Human", "rect": p.Rect(0, 390, 250, 60), "choice": (True, True), "flip": False}
    ]
    for button in buttons:
        button["rect"].centerx = screen.get_width() // 2 - MOVE_LOG_PANEL_WIDTH // 2

    while True:
        title_text = title_font.render("Choose Your Side", True, p.Color("black"))
        screen.blit(title_text, title_text.get_rect(centerx=screen.get_width() // 2 - MOVE_LOG_PANEL_WIDTH // 2, y=80))

        mouse_pos = p.mouse.get_pos()
        for event in p.event.get():
            if event.type == p.QUIT: p.quit(); sys.exit()
            if event.type == p.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        FLIP_BOARD = button["flip"]
                        return button["choice"]

        for button in buttons:
            color = p.Color("lightblue") if button["rect"].collidepoint(mouse_pos) else p.Color("gray")
            p.draw.rect(screen, color, button["rect"], border_radius=8)
            p.draw.rect(screen, p.Color("black"), button["rect"], 3, border_radius=8)
            text = button_font.render(button["text"], True, p.Color("black"))
            screen.blit(text, text.get_rect(center=button["rect"].center))

        p.display.flip()

def main():
    p.init()
    screen_width = BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH + 2 * BORDER_SIZE
    screen_height = BOARD_HEIGHT + BUTTON_PANEL_HEIGHT + 2 * BORDER_SIZE
    screen = p.display.set_mode((screen_width, screen_height))
    clock = p.time.Clock()
    loadImages()

    while True:
        player_one, player_two = showMenuScreen(screen)
        p.display.set_caption("ChessAI")

        game_state = ChessEngine.GameState()
        valid_moves = game_state.getValidMoves()
        move_made = False; animate = False; game_over = False; ai_thinking = False
        move_undone = False; move_finder_process = None; square_selected = ()
        player_clicks = []; ai_score = 0.0; surrendered = False

        running_game = True
        while running_game:
            human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)

            for event in p.event.get():
                if event.type == p.QUIT: p.quit(); sys.exit()
                elif event.type == p.MOUSEBUTTONDOWN:
                    location = p.mouse.get_pos()
                    if not game_over:
                        if BORDER_SIZE < location[0] < BOARD_WIDTH + BORDER_SIZE and BORDER_SIZE < location[1] < BOARD_HEIGHT + BORDER_SIZE:
                            if human_turn:
                                col = (location[0] - BORDER_SIZE) // SQUARE_SIZE
                                row = (location[1] - BORDER_SIZE) // SQUARE_SIZE
                                if FLIP_BOARD: row, col = DIMENSION-1-row, DIMENSION-1-col
                                if square_selected == (row, col): square_selected, player_clicks = (), []
                                else:
                                    square_selected = (row, col); player_clicks.append(square_selected)
                                if len(player_clicks) == 2:
                                    move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                                    for v_move in valid_moves:
                                        if move == v_move:
                                            game_state.makeMove(v_move)
                                            move_made, animate, square_selected, player_clicks = True, True, (), []
                                            break
                                    if not move_made: player_clicks = [square_selected]
                        elif UNDO_BUTTON_RECT.collidepoint(location):
                            if len(game_state.move_log) > 0:
                                undo_count = 1 if player_one and player_two else 2
                                for _ in range(undo_count):
                                    if len(game_state.move_log) > 0: game_state.undoMove()
                                move_made, animate, game_over = True, False, False
                                surrendered = False
                                if ai_thinking: move_finder_process.terminate(); ai_thinking = False
                                move_undone = True
                        elif RESET_BUTTON_RECT.collidepoint(location):
                            game_state = ChessEngine.GameState(); valid_moves = game_state.getValidMoves(); square_selected, player_clicks = (), []; move_made, animate, game_over, surrendered = False, False, False, False
                            if ai_thinking: move_finder_process.terminate(); ai_thinking = False
                        elif MENU_BUTTON_RECT.collidepoint(location):
                            if ai_thinking: move_finder_process.terminate(); ai_thinking = False
                            running_game = False
                        elif SURRENDER_BUTTON_RECT.collidepoint(location) and human_turn:
                            game_over = True
                            surrendered = True
                    elif PLAY_AGAIN_BUTTON_RECT.collidepoint(location):
                        game_state, valid_moves, square_selected, player_clicks, move_made, animate, game_over, surrendered = ChessEngine.GameState(), game_state.getValidMoves(), (), [], False, False, False, False
            
            if not game_over and not human_turn and not move_undone:
                if not ai_thinking:
                    ai_thinking = True
                    return_queue = Queue()
                    move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, AI_THINK_TIME, return_queue))
                    move_finder_process.start()
                if not move_finder_process.is_alive():
                    if not return_queue.empty():
                        ai_move, ai_score = return_queue.get()
                        if ai_move is None and valid_moves: ai_move = random.choice(valid_moves)
                        game_state.makeMove(ai_move)
                        move_made, animate, ai_thinking = True, True, False
                    else: ai_thinking = False

            if move_made:
                valid_moves = game_state.getValidMoves()
                move_made, move_undone = False, False

            drawGameState(screen, game_state, valid_moves, square_selected, ai_score, ai_thinking, human_turn)

            if game_state.checkmate or game_state.stalemate or game_state.isThreefoldRepetition() or surrendered:
                game_over = True
                text = ""
                if surrendered:
                    text = "Black surrenders. White wins!" if not game_state.white_to_move else "White surrenders. Black wins!"
                elif game_state.stalemate: text = "Stalemate"
                elif game_state.isThreefoldRepetition(): text = "Draw by Repetition"
                else: text = "Black wins by checkmate" if game_state.white_to_move else "White wins by checkmate"
                drawEndGameText(screen, text)

            clock.tick(MAX_FPS)
            p.display.flip()

def drawGameState(screen, gs, valid_moves, sq_selected, ai_score, ai_thinking, human_turn):
    screen.fill(p.Color("#212121"))
    drawBoard(screen)
    drawBoardCoordinates(screen)
    highlightSquares(screen, gs, valid_moves, sq_selected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, ai_score, ai_thinking)
    drawButtons(screen, human_turn) # Truyền biến human_turn

def drawBoard(screen):
    colors = [p.Color(238, 238, 210), p.Color(118, 150, 86)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            p.draw.rect(screen, colors[((r+c)%2)], p.Rect(c*SQUARE_SIZE+BORDER_SIZE, r*SQUARE_SIZE+BORDER_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def drawBoardCoordinates(screen):
    font = p.font.SysFont("Arial", 16, True, False)
    coord_color = p.Color("white")
    files, ranks = ['a','b','c','d','e','f','g','h'], ['8','7','6','5','4','3','2','1']
    if FLIP_BOARD: files.reverse(); ranks.reverse()
    for i in range(DIMENSION):
        text = font.render(files[i], True, coord_color)
        screen.blit(text, text.get_rect(centerx=i*SQUARE_SIZE+BORDER_SIZE+SQUARE_SIZE//2, centery=BORDER_SIZE//2))
        screen.blit(text, text.get_rect(centerx=i*SQUARE_SIZE+BORDER_SIZE+SQUARE_SIZE//2, centery=BOARD_HEIGHT+BORDER_SIZE+BORDER_SIZE//2))
        text = font.render(ranks[i], True, coord_color)
        screen.blit(text, text.get_rect(centerx=BORDER_SIZE//2, centery=i*SQUARE_SIZE+BORDER_SIZE+SQUARE_SIZE//2))
        screen.blit(text, text.get_rect(centerx=BOARD_WIDTH+BORDER_SIZE+BORDER_SIZE//2, centery=i*SQUARE_SIZE+BORDER_SIZE+SQUARE_SIZE//2))

def highlightSquares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ('w' if gs.white_to_move else 'b'):
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE)); s.set_alpha(100); s.fill(p.Color('blue'))
            dr, dc = (DIMENSION-1-r, DIMENSION-1-c) if FLIP_BOARD else (r, c)
            screen.blit(s, (dc*SQUARE_SIZE+BORDER_SIZE, dr*SQUARE_SIZE+BORDER_SIZE))
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    edr, edc = (DIMENSION-1-move.end_row, DIMENSION-1-move.end_col) if FLIP_BOARD else (move.end_row, move.end_col)
                    screen.blit(s, (edc*SQUARE_SIZE+BORDER_SIZE, edr*SQUARE_SIZE+BORDER_SIZE))
    if gs.move_log:
        last_move = gs.move_log[-1]; s = p.Surface((SQUARE_SIZE, SQUARE_SIZE)); s.set_alpha(120)
        start_r, start_c = last_move.start_row, last_move.start_col
        end_r, end_c = last_move.end_row, last_move.end_col
        if FLIP_BOARD: start_r, start_c = DIMENSION-1-start_r, DIMENSION-1-start_c; end_r, end_c = DIMENSION-1-end_r, DIMENSION-1-end_c
        s.fill(p.Color("#fde047"))
        screen.blit(s, (start_c*SQUARE_SIZE+BORDER_SIZE, start_r*SQUARE_SIZE+BORDER_SIZE))
        screen.blit(s, (end_c*SQUARE_SIZE+BORDER_SIZE, end_r*SQUARE_SIZE+BORDER_SIZE))

def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                dr, dc = (DIMENSION-1-r, DIMENSION-1-c) if FLIP_BOARD else (r, c)
                screen.blit(IMAGES[piece], p.Rect(dc*SQUARE_SIZE+BORDER_SIZE, dr*SQUARE_SIZE+BORDER_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def drawMoveLog(screen, gs, ai_score, ai_thinking):
    move_log_x = BOARD_WIDTH + 2 * BORDER_SIZE
    move_log_rect = p.Rect(move_log_x, 0, MOVE_LOG_PANEL_WIDTH, screen.get_height())
    p.draw.rect(screen, p.Color("#373737"), move_log_rect)
    font = p.font.SysFont("Arial", 18, True, False); text_color = p.Color("white")
    status_text = "AI is thinking..." if ai_thinking else "Game Over" if gs.checkmate or gs.stalemate else "White's Turn" if gs.white_to_move else "Black's Turn"
    text_obj = font.render(status_text, True, text_color)
    screen.blit(text_obj, text_obj.get_rect(centerx=move_log_x+MOVE_LOG_PANEL_WIDTH//2, y=20))
    score_text = f"Eval: {ai_score:.2f}"
    score_obj = font.render(score_text, True, text_color)
    screen.blit(score_obj, score_obj.get_rect(centerx=move_log_x+MOVE_LOG_PANEL_WIDTH//2, y=50))
    log_font = p.font.SysFont("Consolas", 16); y_padding = 100
    move_texts = []
    for i in range(0, len(gs.move_log), 2):
        move_number = str(i//2 + 1) + "."
        white_move = str(gs.move_log[i])
        black_move = ""
        if i + 1 < len(gs.move_log): black_move = str(gs.move_log[i+1])
        move_texts.append(f"{move_number:<4} {white_move:<10} {black_move:<10}")
    for i, text in enumerate(reversed(move_texts)):
        if y_padding + i*25 > screen.get_height()-20: break
        text_obj = log_font.render(text, True, text_color)
        screen.blit(text_obj, (move_log_x+20, y_padding+i*25))

def drawButtons(screen, human_turn):
    font = p.font.SysFont("Arial", 16, True, False)
    mouse_pos = p.mouse.get_pos()
    buttons = [
        {"rect": UNDO_BUTTON_RECT, "text": "Undo", "base_color": UNDO_COLOR, "hover_color": UNDO_HOVER_COLOR},
        {"rect": RESET_BUTTON_RECT, "text": "Reset", "base_color": RESET_COLOR, "hover_color": RESET_HOVER_COLOR},
        {"rect": MENU_BUTTON_RECT, "text": "Menu", "base_color": MENU_COLOR, "hover_color": MENU_HOVER_COLOR},
        {"rect": SURRENDER_BUTTON_RECT, "text": "Surrender", "base_color": SURRENDER_COLOR, "hover_color": SURRENDER_HOVER_COLOR}
    ]
    for button in buttons:
        color = button["base_color"]
        # Nút Surrender chỉ hoạt động khi đến lượt người chơi
        if button["text"] == "Surrender":
            if not human_turn:
                color = DISABLED_COLOR
            elif button["rect"].collidepoint(mouse_pos):
                color = button["hover_color"]
        elif button["rect"].collidepoint(mouse_pos):
            color = button["hover_color"]
        
        p.draw.rect(screen, color, button["rect"], border_radius=8)
        text = font.render(button["text"], True, p.Color("white"))
        screen.blit(text, text.get_rect(center=button["rect"].center))

def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_obj = font.render(text, True, p.Color('white'))
    text_location = p.Rect(0, 0, BOARD_WIDTH+2*BORDER_SIZE, BOARD_HEIGHT+2*BORDER_SIZE).move((BOARD_WIDTH+2*BORDER_SIZE)/2 - text_obj.get_width()/2, (BOARD_HEIGHT+2*BORDER_SIZE)/2 - text_obj.get_height()/2 - 50)
    s = p.Surface((BOARD_WIDTH+2*BORDER_SIZE, BOARD_HEIGHT+2*BORDER_SIZE)); s.set_alpha(150); s.fill(p.Color("black"))
    screen.blit(s, (0,0))
    screen.blit(text_obj, text_location)
    color = p.Color("lightgreen") if PLAY_AGAIN_BUTTON_RECT.collidepoint(p.mouse.get_pos()) else p.Color("gray")
    p.draw.rect(screen, color, PLAY_AGAIN_BUTTON_RECT, border_radius=8)
    font = p.font.SysFont("Arial", 20, True, False)
    text = font.render("Play Again", True, p.Color("black"))
    screen.blit(text, text.get_rect(center=PLAY_AGAIN_BUTTON_RECT.center))

if __name__ == "__main__":
    main()