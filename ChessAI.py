import random
import time

# --- CÁC HẰNG SỐ LƯỢNG GIÁ ---
CHECKMATE = 1000
STALEMATE = 0
MAX_DEPTH = 10 # Độ sâu tìm kiếm tối đa

# Bảng điểm thưởng cho Tốt Thông
PASSED_PAWN_BONUS = [0, 0.2, 0.4, 0.8, 1.5, 2.5, 4.0, 0] 

# Điểm phạt/thưởng chiến lược
DOUBLED_PAWN_PENALTY = -0.1
ISOLATED_PAWN_PENALTY = -0.15
ROOK_ON_OPEN_FILE_BONUS = 0.4
ROOK_ON_SEMI_OPEN_FILE_BONUS = 0.2
BISHOP_PAIR_BONUS = 0.3

# Các hằng số khác
NULL_MOVE_ALLOWED = True
NULL_MOVE_REDUCTION = 2
LMR_ALLOWED = True
PIECE_VALUES = {"p": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}

# --- BẢNG ĐIỂM VỊ TRÍ (GIỮ NGUYÊN) ---
knight_scores = [[0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0], [0.1, 0.3, 0.5, 0.5, 0.5, 0.5, 0.3, 0.1], [0.2, 0.5, 0.6, 0.65, 0.65, 0.6, 0.5, 0.2], [0.2, 0.55, 0.65, 0.7, 0.7, 0.65, 0.55, 0.2], [0.2, 0.5, 0.65, 0.7, 0.7, 0.65, 0.5, 0.2], [0.2, 0.55, 0.6, 0.65, 0.65, 0.6, 0.55, 0.2], [0.1, 0.3, 0.5, 0.55, 0.55, 0.5, 0.3, 0.1], [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0]]
bishop_scores = [[0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0], [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2], [0.2, 0.4, 0.5, 0.6, 0.6, 0.5, 0.4, 0.2], [0.2, 0.5, 0.5, 0.6, 0.6, 0.5, 0.5, 0.2], [0.2, 0.4, 0.6, 0.6, 0.6, 0.6, 0.4, 0.2], [0.2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.2], [0.2, 0.5, 0.4, 0.4, 0.4, 0.4, 0.5, 0.2], [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0]]
rook_scores = [[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], [0.5, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.5], [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0], [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0], [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0], [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0], [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0], [0.25, 0.25, 0.25, 0.5, 0.5, 0.25, 0.25, 0.25]]
queen_scores = [[0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0], [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2], [0.2, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2], [0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3], [0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3], [0.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2], [0.2, 0.4, 0.5, 0.4, 0.4, 0.4, 0.4, 0.2], [0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0]]
pawn_scores = [[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8], [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7], [0.3, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0.3], [0.25, 0.25, 0.3, 0.45, 0.45, 0.3, 0.25, 0.25], [0.2, 0.2, 0.2, 0.4, 0.4, 0.2, 0.2, 0.2], [0.25, 0.15, 0.1, 0.2, 0.2, 0.1, 0.15, 0.25], [0.25, 0.3, 0.3, 0.0, 0.0, 0.3, 0.3, 0.25], [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]]
piece_position_scores = {"wN": knight_scores, "bN": knight_scores[::-1], "wB": bishop_scores, "bB": bishop_scores[::-1], "wQ": queen_scores, "bQ": queen_scores[::-1], "wR": rook_scores, "bR": rook_scores[::-1], "wp": pawn_scores, "bp": pawn_scores[::-1]}

# --- HÀM LƯỢNG GIÁ CHIẾN LƯỢC ---
def scoreBoard(game_state):
    if game_state.checkmate: return -CHECKMATE if game_state.white_to_move else CHECKMATE
    if game_state.stalemate: return STALEMATE
    score = 0; white_bishops = 0; black_bishops = 0
    white_pawn_files = [0] * 8; black_pawn_files = [0] * 8
    for r in range(8):
        for c in range(8):
            piece = game_state.board[r][c]
            if piece != "--":
                piece_color, piece_type = piece[0], piece[1]
                score_for_piece = PIECE_VALUES[piece_type]
                if piece_type != 'K': score_for_piece += piece_position_scores[piece][r][c]
                if piece_color == 'w':
                    score += score_for_piece
                    if piece_type == 'B': white_bishops += 1
                    if piece_type == 'p': white_pawn_files[c] += 1
                else:
                    score -= score_for_piece
                    if piece_type == 'B': black_bishops += 1
                    if piece_type == 'p': black_pawn_files[c] += 1
    for r in range(8):
        for c in range(8):
            piece = game_state.board[r][c]
            if piece != "--":
                piece_color, piece_type = piece[0], piece[1]
                if piece_type == 'p':
                    if (piece_color == 'w' and white_pawn_files[c] > 1) or \
                       (piece_color == 'b' and black_pawn_files[c] > 1):
                        if piece_color == 'w': score += DOUBLED_PAWN_PENALTY
                        else: score -= DOUBLED_PAWN_PENALTY
                    if (c == 0 or (piece_color == 'w' and white_pawn_files[c-1] == 0) or (piece_color == 'b' and black_pawn_files[c-1] == 0)) and \
                       (c == 7 or (piece_color == 'w' and white_pawn_files[c+1] == 0) or (piece_color == 'b' and black_pawn_files[c+1] == 0)):
                        if piece_color == 'w': score += ISOLATED_PAWN_PENALTY
                        else: score -= ISOLATED_PAWN_PENALTY
                    is_passed = True
                    if piece_color == 'w':
                        for i in range(r - 1, -1, -1):
                            if (c > 0 and game_state.board[i][c-1] == 'bp') or \
                               (game_state.board[i][c] == 'bp') or \
                               (c < 7 and game_state.board[i][c+1] == 'bp'): is_passed = False; break
                        if is_passed: score += PASSED_PAWN_BONUS[7-r]
                    else:
                        for i in range(r + 1, 8):
                            if (c > 0 and game_state.board[i][c-1] == 'wp') or \
                               (game_state.board[i][c] == 'wp') or \
                               (c < 7 and game_state.board[i][c+1] == 'wp'): is_passed = False; break
                        if is_passed: score -= PASSED_PAWN_BONUS[r]
                elif piece_type == 'R':
                    if white_pawn_files[c] == 0 and black_pawn_files[c] == 0:
                        if piece_color == 'w': score += ROOK_ON_OPEN_FILE_BONUS
                        else: score -= ROOK_ON_OPEN_FILE_BONUS
                    elif (piece_color == 'w' and white_pawn_files[c] == 0) or \
                         (piece_color == 'b' and black_pawn_files[c] == 0):
                        if piece_color == 'w': score += ROOK_ON_SEMI_OPEN_FILE_BONUS
                        else: score -= ROOK_ON_SEMI_OPEN_FILE_BONUS
    if white_bishops >= 2: score += BISHOP_PAIR_BONUS
    if black_bishops >= 2: score -= BISHOP_PAIR_BONUS
    return score

# --- CÁC HÀM TÌM KIẾM ---
class SearchData:
    def __init__(self):
        self.candidate_move = None
        self.start_time = 0; self.time_limit = 0
        self.killer_moves = [[None, None] for _ in range(MAX_DEPTH + 1)]

def findBestMove(game_state, valid_moves, time_limit, return_queue):
    data = SearchData()
    data.time_limit = time_limit
    data.start_time = time.time()
    best_move_from_completed_depth = None
    best_score_from_completed_depth = 0
    for depth in range(1, MAX_DEPTH + 1):
        score = findMoveNegaMaxAlphaBeta(game_state, valid_moves, depth, 0, -CHECKMATE, CHECKMATE, 1 if game_state.white_to_move else -1, data)
        if time.time() - data.start_time < data.time_limit:
            best_move_from_completed_depth = data.candidate_move
            best_score_from_completed_depth = score
            print(f"Depth {depth}: Best move is {best_move_from_completed_depth}, Score: {best_score_from_completed_depth:.2f}")
            
            # --- CẢI TIẾN: DỪNG LẠI NGAY KHI TÌM THẤY NƯỚC CHIẾU BÍ ---
            # Điểm chiếu bí thường gần bằng CHECKMATE. Ta dùng ngưỡng để bắt.
            if best_score_from_completed_depth > CHECKMATE - MAX_DEPTH:
                print("Checkmate found! Ending search early.")
                break # Thoát khỏi vòng lặp tìm kiếm sâu dần
        else:
            print(f"Time limit reached during depth {depth}. Using best move from depth {depth - 1}.")
            break
    if best_move_from_completed_depth is None and valid_moves:
        best_move_from_completed_depth = random.choice(valid_moves)
    return_queue.put((best_move_from_completed_depth, best_score_from_completed_depth))

def orderMoves(moves, game_state, data, ply):
    move_scores = []
    for move in moves:
        score = 0
        if move.is_capture:
            victim_val = PIECE_VALUES[move.piece_captured[1]]
            attacker_val = PIECE_VALUES[move.piece_moved[1]]
            score += 1000 + victim_val * 10 - attacker_val
        elif move in data.killer_moves[ply]: score += 900
        if move.is_pawn_promotion: score += 800
        move_scores.append((score, move))
    move_scores.sort(key=lambda x: x[0], reverse=True)
    return [move for score, move in move_scores]

def findMoveNegaMaxAlphaBeta(game_state, valid_moves, depth, ply, alpha, beta, turn, data):
    if time.time() - data.start_time > data.time_limit: return 0
    if ply >= MAX_DEPTH: return turn * scoreBoard(game_state)
    if depth <= 0: return turn * scoreBoard(game_state)
    if NULL_MOVE_ALLOWED and depth >= 3 and not game_state.inCheck() and ply > 0:
        game_state.white_to_move = not game_state.white_to_move
        original_enpassant = game_state.enpassant_possible; game_state.enpassant_possible = ()
        score = -findMoveNegaMaxAlphaBeta(game_state, valid_moves, depth - 1 - NULL_MOVE_REDUCTION, ply + 1, -beta, -beta + 1, -turn, data)
        game_state.white_to_move = not game_state.white_to_move
        game_state.enpassant_possible = original_enpassant
        if score >= beta: return beta
    ordered_moves = orderMoves(valid_moves, game_state, data, ply)
    if not ordered_moves: return -CHECKMATE if game_state.inCheck() else STALEMATE
    for i, move in enumerate(ordered_moves):
        game_state.makeMove(move)
        next_moves = game_state.getValidMoves()
        score = 0
        if LMR_ALLOWED and depth >= 3 and i >= 3 and not game_state.inCheck() and not move.is_capture and not move.is_pawn_promotion:
            reduction = 1
            score = -findMoveNegaMaxAlphaBeta(game_state, next_moves, depth - 1 - reduction, ply + 1, -alpha - 1, -alpha, -turn, data)
            if score > alpha and score < beta:
                score = -findMoveNegaMaxAlphaBeta(game_state, next_moves, depth - 1, ply + 1, -beta, -alpha, -turn, data)
        else:
            score = -findMoveNegaMaxAlphaBeta(game_state, next_moves, depth - 1, ply + 1, -beta, -alpha, -turn, data)
        game_state.undoMove()
        if time.time() - data.start_time > data.time_limit: return 0
        if score > alpha:
            alpha = score
            if ply == 0: data.candidate_move = move
        if alpha >= beta:
            if not move.is_capture:
                if move != data.killer_moves[ply][0]:
                    data.killer_moves[ply][1] = data.killer_moves[ply][0]
                    data.killer_moves[ply][0] = move
            break
    return alpha