import random

piece_score = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}

# Giữ nguyên piece-square tables (đã tốt rồi)
knight_scores = [[0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0],
                 [0.1, 0.3, 0.5, 0.5, 0.5, 0.5, 0.3, 0.1],
                 [0.2, 0.5, 0.6, 0.65, 0.65, 0.6, 0.5, 0.2],
                 [0.2, 0.55, 0.65, 0.7, 0.7, 0.65, 0.55, 0.2],
                 [0.2, 0.5, 0.65, 0.7, 0.7, 0.65, 0.5, 0.2],
                 [0.2, 0.55, 0.6, 0.65, 0.65, 0.6, 0.55, 0.2],
                 [0.1, 0.3, 0.5, 0.55, 0.55, 0.5, 0.3, 0.1],
                 [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0]]

bishop_scores = [[0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
                 [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
                 [0.2, 0.4, 0.5, 0.6, 0.6, 0.5, 0.4, 0.2],
                 [0.2, 0.5, 0.5, 0.6, 0.6, 0.5, 0.5, 0.2],
                 [0.2, 0.4, 0.6, 0.6, 0.6, 0.6, 0.4, 0.2],
                 [0.2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.2],
                 [0.2, 0.5, 0.4, 0.4, 0.4, 0.4, 0.5, 0.2],
                 [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0]]

rook_scores = [[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
               [0.5, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.5],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.25, 0.25, 0.25, 0.5, 0.5, 0.25, 0.25, 0.25]]

queen_scores = [[0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0],
                [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
                [0.2, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
                [0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
                [0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
                [0.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
                [0.2, 0.4, 0.5, 0.4, 0.4, 0.4, 0.4, 0.2],
                [0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0]]

pawn_scores = [[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
               [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
               [0.3, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0.3],
               [0.25, 0.25, 0.3, 0.45, 0.45, 0.3, 0.25, 0.25],
               [0.2, 0.2, 0.2, 0.4, 0.4, 0.2, 0.2, 0.2],
               [0.25, 0.15, 0.1, 0.2, 0.2, 0.1, 0.15, 0.25],
               [0.25, 0.3, 0.3, 0.0, 0.0, 0.3, 0.3, 0.25],
               [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]]

piece_position_scores = {"wN": knight_scores,
                         "bN": knight_scores[::-1],
                         "wB": bishop_scores,
                         "bB": bishop_scores[::-1],
                         "wQ": queen_scores,
                         "bQ": queen_scores[::-1],
                         "wR": rook_scores,
                         "bR": rook_scores[::-1],
                         "wp": pawn_scores,
                         "bp": pawn_scores[::-1]}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 4  # Tăng từ 3 lên 4


def orderMoves(moves, game_state):
    """Move ordering đơn giản để cải thiện alpha-beta pruning"""
    scored_moves = []

    for move in moves:
        score = 0

        # Ưu tiên nước ăn quân
        if move.piece_captured != "--":
            score += piece_score[move.piece_captured[1]] * 10

        # Ưu tiên nước chiếu tướng
        game_state.makeMove(move)
        if game_state.inCheck():
            score += 60  # Ưu tiên cao cho chiếu tướng
        game_state.undoMove()

        # Ưu tiên lên tốt
        if move.is_pawn_promotion:
            score += 70

        # Ưu tiên nhập thành
        if move.is_castle_move:
            score += 50

        # Ưu tiên di chuyển vào trung tâm
        if (move.end_row, move.end_col) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
            score += 5


        # Penalty for moves leading to repetition
        game_state.makeMove(move)
        position_key = game_state.boardToString()
        if game_state.position_count.get(position_key, 0) >= 2:
            score -= 100  # Heavy penalty for repetition
        game_state.undoMove()

        scored_moves.append((score, move))
    # Sắp xếp theo điểm giảm dần
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    return [move for _, move in scored_moves]


def isHangingPiece(game_state, row, col):
    """Kiểm tra quân có bị treo không (đơn giản)"""
    piece = game_state.board[row][col]
    if piece == "--" or piece[1] == "K":
        return False

    piece_color = piece[0]

    # Kiểm tra có bị tấn công không
    attacked = False
    defended = False

    for r in range(8):
        for c in range(8):
            enemy_piece = game_state.board[r][c]
            if enemy_piece == "--":
                continue

            # Kiểm tra enemy có thể tấn công không
            if enemy_piece[0] != piece_color:
                if canAttack(game_state, r, c, row, col):
                    attacked = True

            # Kiểm tra ally có thể bảo vệ không
            elif enemy_piece[0] == piece_color and (r != row or c != col):
                if canAttack(game_state, r, c, row, col):
                    defended = True

    return attacked and not defended


def canAttack(game_state, from_row, from_col, to_row, to_col):
    """Kiểm tra quân có thể tấn công ô target không (đơn giản)"""
    piece = game_state.board[from_row][from_col]
    if piece == "--":
        return False

    piece_type = piece[1]
    row_diff = to_row - from_row
    col_diff = to_col - from_col

    # Pawn attacks
    if piece_type == "p":
        direction = -1 if piece[0] == "w" else 1
        return row_diff == direction and abs(col_diff) == 1

    # Knight attacks
    elif piece_type == "N":
        return (abs(row_diff) == 2 and abs(col_diff) == 1) or \
            (abs(row_diff) == 1 and abs(col_diff) == 2)

    # King attacks
    elif piece_type == "K":
        return abs(row_diff) <= 1 and abs(col_diff) <= 1 and (row_diff != 0 or col_diff != 0)

    # Sliding pieces (Bishop, Rook, Queen)
    elif piece_type in "BRQ":
        if piece_type == "B" and abs(row_diff) != abs(col_diff):
            return False
        if piece_type == "R" and row_diff != 0 and col_diff != 0:
            return False
        if piece_type == "Q" and row_diff != 0 and col_diff != 0 and abs(row_diff) != abs(col_diff):
            return False

        # Check if path is clear
        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = from_row + step_row
        current_col = from_col + step_col

        while current_row != to_row or current_col != to_col:
            if game_state.board[current_row][current_col] != "--":
                return False
            current_row += step_row
            current_col += step_col

        return True

    return False


def findBestMove(game_state, valid_moves, return_queue):
    global next_move
    next_move = None

    # Move ordering để cải thiện hiệu suất
    ordered_moves = orderMoves(valid_moves, game_state)

    findMoveNegaMaxAlphaBeta(game_state, ordered_moves, DEPTH, -CHECKMATE, CHECKMATE,
                             1 if game_state.white_to_move else -1)
    return_queue.put(next_move)


def findMoveNegaMaxAlphaBeta(game_state, valid_moves, depth, alpha, beta, turn_multiplier):
    global next_move
    if depth == 0:
        return turn_multiplier * scoreBoard(game_state)

    max_score = -CHECKMATE
    for move in valid_moves:
        game_state.makeMove(move)
        next_moves = game_state.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(game_state, next_moves, depth - 1, -beta, -alpha, -turn_multiplier)

        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move

        game_state.undoMove()

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break  # Alpha-beta cutoff

    return max_score


def scoreBoard(game_state):
    """Evaluation function cải tiến"""
    if game_state.checkmate:
        if game_state.white_to_move:
            return -CHECKMATE  # black wins
        else:
            return CHECKMATE  # white wins
    elif game_state.stalemate:
        return STALEMATE

    score = 0

    for row in range(8):
        for col in range(8):
            piece = game_state.board[row][col]
            if piece != "--":
                # Material score
                piece_value = piece_score[piece[1]]

                # Position score
                piece_position_score = 0
                if piece[1] != "K":
                    piece_position_score = piece_position_scores[piece][row][col]

                # Hanging piece penalty (QUAN TRỌNG!)
                hanging_penalty = 0
                if piece[1] != "K" and piece[1] != "p":  # Chỉ check các quân quan trọng
                    if isHangingPiece(game_state, row, col):
                        hanging_penalty = piece_value * 0.8  # Penalty 80% giá trị quân

                total_value = piece_value + piece_position_score - hanging_penalty

                if piece[0] == "w":
                    score += total_value
                else:
                    score -= total_value

    return score


def findRandomMove(valid_moves):
    """Picks and returns a random valid move."""
    return random.choice(valid_moves)