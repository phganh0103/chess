# Dùng pygame để tạo giao diện đồ họa
import pygame as p
import ChessEngine, ChessAI  # Engine : quản lý logic chess,AI: tạo nước đi cho AI
import sys
from multiprocessing import Process, Queue
import os

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250  # độ dài của bảng ghi chép nước đi
FLIP_BOARD = False  # Biến để track có flip board không
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8  # số hàng,cột trên bàn cờ
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
UNDO_BUTTON_WITDH = 100
UNDO_BUTTON_HEIGHT = 40
UNDO_BUTTON_X = BOARD_WIDTH // 2 - UNDO_BUTTON_WITDH // 2
UNDO_BUTTON_Y = BOARD_HEIGHT + 10
BUTTON_PANEL_HEIGHT = 60

PLAY_AGAIN_BUTTON_WIDTH = 120
PLAY_AGAIN_BUTTON_HEIGHT = 60
PLAY_AGAIN_BUTTON_X = BOARD_WIDTH // 2 - PLAY_AGAIN_BUTTON_WIDTH // 2
PLAY_AGAIN_BUTTON_Y = BOARD_HEIGHT // 2 + 50
colors = [p.Color("white"), p.Color("gray")]

# Tải ảnh quân cờ từ thư mục /images
# Lưu vào biến toàn cục IMAGES để sử dụng khi vẽ
def loadImages():
    base_path = os.path.dirname(__file__)  # Lấy đường dẫn thư mục hiện tại (chess/)
    image_folder = os.path.join(base_path, "images")
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        path = os.path.join(image_folder, piece + ".png")
        IMAGES[piece] = p.transform.scale(p.image.load(path), (SQUARE_SIZE, SQUARE_SIZE))


def showColorSelectionScreen(screen):
    """
    Hiển thị màn hình chọn màu cờ với GUI
    Returns: (player_one, player_two)
    """
    global FLIP_BOARD

    # Màu và font
    WHITE = p.Color("white")
    BLACK = p.Color("black")
    GRAY = p.Color("gray")
    BLUE = p.Color("lightblue")
    GREEN = p.Color("lightgreen")

    title_font = p.font.SysFont("Arial", 36, True, False)
    button_font = p.font.SysFont("Arial", 20, True, False)

    # Kích thước buttons
    button_width = 250
    button_height = 60
    button_spacing = 80
    start_y = 150

    # Tạo buttons
    buttons = [
        {"text": "Play as White",
         "rect": p.Rect(BOARD_WIDTH // 2 - button_width // 2, start_y, button_width, button_height),
         "choice": (True, False), "flip": False},
        {"text": "Play as Black",
         "rect": p.Rect(BOARD_WIDTH // 2 - button_width // 2, start_y + button_spacing, button_width, button_height),
         "choice": (False, True), "flip": True},
        {"text": "Watch AI vs AI",
         "rect": p.Rect(BOARD_WIDTH // 2 - button_width // 2, start_y + button_spacing * 2, button_width,
                        button_height), "choice": (False, False), "flip": False},
        {"text": "Human vs Human",
         "rect": p.Rect(BOARD_WIDTH // 2 - button_width // 2, start_y + button_spacing * 3, button_width,
                        button_height), "choice": (True, True), "flip": False}
    ]

    clock = p.time.Clock()

    while True:
        # Xử lý events
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()
                # Kiểm tra click vào button nào
                for button in buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        FLIP_BOARD = button["flip"]  # Set flip board
                        return button["choice"]  # Trả về player config

        # Vẽ background
        screen.fill(WHITE)

        # Vẽ title
        title_text = title_font.render("Choose Your Side", True, BLACK)
        title_rect = title_text.get_rect(center=(BOARD_WIDTH // 2, 80))
        screen.blit(title_text, title_rect)

        # Vẽ buttons
        mouse_pos = p.mouse.get_pos()
        for button in buttons:
            # Highlight button khi hover
            color = BLUE if button["rect"].collidepoint(mouse_pos) else GRAY
            p.draw.rect(screen, color, button["rect"])
            p.draw.rect(screen, BLACK, button["rect"], 3)

            # Vẽ text
            text = button_font.render(button["text"], True, BLACK)
            text_rect = text.get_rect(center=button["rect"].center)
            screen.blit(text, text_rect)

        # Vẽ instructions
        instruction_font = p.font.SysFont("Arial", 16, False, False)
        instruction_text = instruction_font.render("Click on your preferred game mode", True, GRAY)
        instruction_rect = instruction_text.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT - 50))
        screen.blit(instruction_text, instruction_rect)

        p.display.flip()
        clock.tick(MAX_FPS)


def main():
    """
    Main driver cho game. Xử lý user input và update graphics
    """
    p.init()
    BUTTON_PANEL_HEIGHT = 60
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT + BUTTON_PANEL_HEIGHT))
    p.display.set_caption("Chess Game - Select Mode")
    clock = p.time.Clock()

    # Load images trước
    loadImages()

    # Hiển thị màn hình chọn màu
    player_one, player_two = showColorSelectionScreen(screen)

    # Setup game sau khi chọn
    p.display.set_caption("Chess Game")
    screen.fill(p.Color("white"))
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    undo_button_font = p.font.SysFont("Arial", 20, True, False)
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False
    animate = False
    square_selected = ()  # no square is selected, keep track of the last click of the user (tuple: (row, col))
    player_clicks = []  # keep track of player clicks (two tuples: [(6, 4), (4, 4)])
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_text = []

    while True:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)

        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
                p.quit()
                sys.exit()
            # mouse handler
            elif event.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # (x, y) location of mouse
                    if location[0] < BOARD_WIDTH and location[1] < BOARD_HEIGHT:
                        # Chuyển đổi tọa độ mouse thành board coordinates
                        col = location[0] // SQUARE_SIZE
                        row = location[1] // SQUARE_SIZE

                        # Nếu board bị flip, cần đảo ngược tọa độ
                        if FLIP_BOARD:
                            row = DIMENSION - 1 - row
                            col = DIMENSION - 1 - col

                        if square_selected == (row, col) or not human_turn:  # user clicked the same square twice
                            square_selected = ()  # deselect
                            player_clicks = []  # clear player clicks
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)  # append for both 1st and 2nd clicks
                        if len(player_clicks) == 2 and human_turn:  # after 2nd click
                            move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                            print(move.getChessNotation())
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    game_state.makeMove(valid_moves[i])
                                    move_made = True
                                    animate = True
                                    square_selected = ()  # reset user clicks
                                    player_clicks = []
                            if not move_made:
                                player_clicks = [square_selected]

                    # Kiểm tra click vào undo button
                    elif BOARD_WIDTH <= location[0] <= BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH and BOARD_HEIGHT <= location[
                        1] <= BOARD_HEIGHT + 30:
                        if len(game_state.move_log) > 0:
                            # Undo 2 moves (player + AI)
                            game_state.undoMove()
                            if len(game_state.move_log) > 0:
                                game_state.undoMove()
                            move_made = True
                            animate = False
                            game_over = False
                            if ai_thinking:
                                move_finder_process.terminate()
                                ai_thinking = False
                            move_undone = True

                    # Kiểm tra click vào reset button
                    elif BOARD_WIDTH <= location[0] <= BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH and BOARD_HEIGHT + 30 <= \
                            location[1] <= BOARD_HEIGHT + 60:
                        game_state = ChessEngine.GameState()
                        valid_moves = game_state.getValidMoves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = True

            # key handlers
            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:  # undo when 'z' is pressed
                    if len(game_state.move_log) > 0:
                        # Undo 2 moves (player + AI)
                        game_state.undoMove()
                        if len(game_state.move_log) > 0:
                            game_state.undoMove()
                        move_made = True
                        animate = False
                        game_over = False
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = True
                elif event.key == p.K_r:  # reset the board when 'r' is pressed
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # AI move finder logic
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                print("thinking...")
                return_queue = Queue()
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()  # call findBestMove(game_state, valid_moves, return_queue)

            if not move_finder_process.is_alive():
                print("done thinking")
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected, move_log_font, undo_button_font)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, 'Black wins by checkmate')
            else:
                drawEndGameText(screen, 'White wins by checkmate')

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, 'Stalemate')

        elif game_state.isThreefoldRepetition():
            game_over = True
            drawEndGameText(screen, 'Draw by threefold repetition')

        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, game_state, valid_moves, square_selected, move_log_font, undo_button_font):
    """
    Vẽ toàn bộ game state hiện tại
    """
    drawBoard(screen)  # Vẽ bàn cờ
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # Vẽ quân cờ
    drawMoveLog(screen, game_state, move_log_font)
    drawUndoButton(screen, undo_button_font)
    drawResetButton(screen, undo_button_font)


# Vẽ toàn bộ trạng thái bàn cờ
# Vẽ các ô bàn cờ (đen/trắng xen kẽ)
def drawBoard(screen):
    """
    Vẽ bàn cờ với khả năng flip cho người chơi đen
    """
    global FLIP_BOARD
    colors = [p.Color("white"), p.Color("gray")]

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            # Nếu flip board, đảo ngược tọa độ
            display_row = (DIMENSION - 1 - row) if FLIP_BOARD else row
            display_col = (DIMENSION - 1 - col) if FLIP_BOARD else col

            color = colors[((row + col) % 2)]
            p.draw.rect(screen, color,
                        p.Rect(display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


# Tô sáng
def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight ô được chọn và các nước đi hợp lệ với flip board support
    """
    global FLIP_BOARD

    if len(game_state.move_log) > 0:
        last_move = game_state.move_log[-1]

        # Highlight ô đi từ (start square)
        start_row, start_col = last_move.start_row, last_move.start_col
        display_start_row = (DIMENSION - 1 - start_row) if FLIP_BOARD else start_row
        display_start_col = (DIMENSION - 1 - start_col) if FLIP_BOARD else start_col
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('yellow'))
        screen.blit(s, (display_start_col * SQUARE_SIZE, display_start_row * SQUARE_SIZE))

        # Highlight ô đi đến (end square)
        end_row, end_col = last_move.end_row, last_move.end_col
        display_end_row = (DIMENSION - 1 - end_row) if FLIP_BOARD else end_row
        display_end_col = (DIMENSION - 1 - end_col) if FLIP_BOARD else end_col
        s.fill(p.Color('green'))
        screen.blit(s, (display_end_col * SQUARE_SIZE, display_end_row * SQUARE_SIZE))

    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'):
            # Highlight ô được chọn
            display_row = (DIMENSION - 1 - row) if FLIP_BOARD else row
            display_col = (DIMENSION - 1 - col) if FLIP_BOARD else col
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

            # Highlight các nước đi hợp lệ
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    display_move_row = (DIMENSION - 1 - move.end_row) if FLIP_BOARD else move.end_row
                    display_move_col = (DIMENSION - 1 - move.end_col) if FLIP_BOARD else move.end_col
                    screen.blit(s, (display_move_col * SQUARE_SIZE, display_move_row * SQUARE_SIZE))

#  Vẽ tất cả quân cờ lên bàn theo trạng thái board
def drawPieces(screen, board):
    """
    Vẽ quân cờ với khả năng flip board
    """
    global FLIP_BOARD

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":  # Không phải ô trống
                # Nếu flip board, đảo ngược vị trí hiển thị
                display_row = (DIMENSION - 1 - row) if FLIP_BOARD else row
                display_col = (DIMENSION - 1 - col) if FLIP_BOARD else col

                screen.blit(IMAGES[piece],
                            p.Rect(display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def drawMoveLog(screen, game_state, font):
    """
    Draws the move log.

    """
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('white'), move_log_rect)

    # Vẽ tiêu đề cột
    header_y = 5
    header_font = p.font.SysFont("Arial", 16, True, False)
    headers = ["Move", "White", "Black"]
    col_widths = [40, 100, 100]
    col_x = [BOARD_WIDTH, BOARD_WIDTH + 80, BOARD_WIDTH + 160]

    for i, header in enumerate(headers):
        text = header_font.render(header, True, p.Color('black'))
        screen.blit(text, (col_x[i] + 5, header_y))

    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_number = str(i // 2 + 1)
        white_move = str(move_log[i]) if i < len(move_log) else ""
        black_move = str(move_log[i + 1]) if i + 1 < len(move_log) else ""
        move_texts.append((move_number, white_move, black_move))

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = header_y + 25

    for move_number, white_move, black_move in move_texts:
        text = font.render(move_number, True, p.Color('black'))
        screen.blit(text, (col_x[0] + padding, text_y))

        text = font.render(white_move, True, p.Color('black'))
        screen.blit(text, (col_x[1] + padding, text_y))

        text = font.render(black_move, True, p.Color('black'))
        screen.blit(text, (col_x[2] + padding, text_y))
        text_y = text.get_height() + line_spacing


def drawResetButton(screen, font):
    """
    Vẽ Reset button
    """
    reset_text = font.render("Reset", True, p.Color("black"))
    reset_button = p.Rect(BOARD_WIDTH, BOARD_HEIGHT + 30, MOVE_LOG_PANEL_WIDTH, 30)

    # Kiểm tra hover
    mouse_pos = p.mouse.get_pos()
    button_color = p.Color("lightcoral") if reset_button.collidepoint(mouse_pos) else p.Color("lightgray")

    p.draw.rect(screen, button_color, reset_button)
    p.draw.rect(screen, p.Color("black"), reset_button, 2)
    screen.blit(reset_text, (reset_button.x + 10, reset_button.y + 5))


# Hiển thị dòng thông báo khi kết thúc ván (checkmate/stalemate)
def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


# Thực hiện hiệu ứng di chuyển quân cờ từng frame
def animateMove(move, screen, board, clock):
    """
    Animating a move với flip board support
    """
    global colors, FLIP_BOARD

    # Tính toán tọa độ display cho animation
    if FLIP_BOARD:
        start_display_row = DIMENSION - 1 - move.start_row
        start_display_col = DIMENSION - 1 - move.start_col
        end_display_row = DIMENSION - 1 - move.end_row
        end_display_col = DIMENSION - 1 - move.end_col
    else:
        start_display_row = move.start_row
        start_display_col = move.start_col
        end_display_row = move.end_row
        end_display_col = move.end_col

    d_row = end_display_row - start_display_row
    d_col = end_display_col - start_display_col
    frames_per_square = 5  # frames to move one square
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square

    for frame in range(frame_count + 1):
        # Tính vị trí hiện tại của animation
        current_row = start_display_row + d_row * frame / frame_count
        current_col = start_display_col + d_col * frame / frame_count

        # Vẽ lại toàn bộ board
        drawBoard(screen)
        drawPieces(screen, board)

        # Xóa piece ở vị trí cuối
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(end_display_col * SQUARE_SIZE, end_display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)

        # Vẽ captured piece nếu có
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                # En passant special case
                if FLIP_BOARD:
                    enpassant_display_row = DIMENSION - 1 - (
                        move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1)
                    enpassant_display_col = DIMENSION - 1 - move.end_col
                else:
                    enpassant_display_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                    enpassant_display_col = move.end_col
                end_square = p.Rect(enpassant_display_col * SQUARE_SIZE, enpassant_display_row * SQUARE_SIZE,
                                    SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)

        # Vẽ moving piece tại vị trí animation
        screen.blit(IMAGES[move.piece_moved],
                    p.Rect(current_col * SQUARE_SIZE, current_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        p.display.flip()
        clock.tick(60)

def drawUndoButton(screen, font):
    """
    Vẽ Undo button
    """
    undo_text = font.render("Undo", True, p.Color("black"))
    undo_button = p.Rect(BOARD_WIDTH, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, 30)

    # Kiểm tra hover
    mouse_pos = p.mouse.get_pos()
    button_color = p.Color("lightblue") if undo_button.collidepoint(mouse_pos) else p.Color("lightgray")

    p.draw.rect(screen, button_color, undo_button)
    p.draw.rect(screen, p.Color("black"), undo_button, 2)
    screen.blit(undo_text, (undo_button.x + 10, undo_button.y + 5))


def drawAgainButton(screen, font):
    """
    Draw again button
    :param screen:
    :param font:
    :return:
    """

    button_rect = p.Rect(PLAY_AGAIN_BUTTON_X, PLAY_AGAIN_BUTTON_Y, PLAY_AGAIN_BUTTON_WIDTH, PLAY_AGAIN_BUTTON_HEIGHT)
    p.draw.rect(screen, p.Color('white'), button_rect)
    p.draw.rect(screen, p.Color('black'), button_rect, 2)
    text = font.render("Play Again", True, p.Color('black'))
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)
    return button_rect


if __name__ == "__main__":
    main()
