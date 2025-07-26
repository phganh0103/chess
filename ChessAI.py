import random
import time

# Biến global để theo dõi lịch sử vị trí
position_history = {}


def order_moves_tactical(moves, game_state):
    """Sắp xếp nước đi với tactical awareness"""
    scored_moves = []

    for move in moves:
        score = 0

        # 1. Ưu tiên nước ăn quân với SEE (Static Exchange Evaluation)
        if move.piece_captured != "--":
            see_score = static_exchange_evaluation(game_state, move)
            if see_score > 0:
                score += 1000 + see_score
            else:
                score += see_score  # Có thể âm nếu ăn quân không có lợi

        # 2. Kiểm tra tactical patterns
        game_state.makeMove(move)

        # Tactical bonuses
        score += check_tactical_patterns(game_state, move)

        # Kiểm tra nước đi có dẫn đến lặp lại không
        position_key = get_position_key(game_state)
        if is_repetition_move(position_key, game_state):
            if is_winning_position(game_state):
                score -= 2000
            else:
                score -= 100

        # Ưu tiên chiếu tướng
        if game_state.inCheck():
            score += 500

        game_state.undoMove()

        # 3. Ưu tiên lên tốt
        if move.is_pawn_promotion:
            score += 800

        # 4. Ưu tiên nhập thành
        if move.is_castle_move:
            score += 300

        # 5. Ưu tiên kiểm soát trung tâm
        if (move.end_row, move.end_col) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
            score += 50

        scored_moves.append((score, move))

    scored_moves.sort(reverse=True, key=lambda x: x[0])
    return [move for _, move in scored_moves]


def static_exchange_evaluation(game_state, move):
    """Đánh giá trao đổi quân cờ tĩnh"""
    if move.piece_captured == "--":
        return 0

    # Giá trị quân bị ăn
    captured_value = piece_values[move.piece_captured[1]]["mg"]

    # Giá trị quân tấn công
    attacker_value = piece_values[move.piece_moved[1]]["mg"]

    # Đơn giản: nếu ăn quân đắt hơn quân tấn công
    if captured_value >= attacker_value:
        return captured_value - attacker_value + 0.1

    # Nếu ăn quân rẻ hơn, kiểm tra có bị ăn lại không
    game_state.makeMove(move)
    target_square = (move.end_row, move.end_col)
    is_defended = is_square_attacked(game_state, target_square[0], target_square[1],
                                     "b" if game_state.white_to_move else "w")
    game_state.undoMove()

    if is_defended:
        return captured_value - attacker_value
    else:
        return captured_value


def check_tactical_patterns(game_state, move):
    """Kiểm tra các pattern chiến thuật"""
    score = 0

    # 1. Fork (tấn công 2 quân cùng lúc)
    fork_targets = count_fork_targets(game_state, move.end_row, move.end_col, move.piece_moved)
    if fork_targets >= 2:
        score += 200 * fork_targets

    # 2. Pin (ghim quân)
    if is_creating_pin(game_state, move):
        score += 150

    # 3. Skewer (xiên que)
    if is_creating_skewer(game_state, move):
        score += 180

    # 4. Discovered attack (tấn công phát hiện)
    if is_discovered_attack(game_state, move):
        score += 120

    return score


def count_fork_targets(game_state, row, col, piece):
    """Đếm số quân địch có thể tấn công từ vị trí này"""
    targets = 0
    enemy_color = "b" if piece[0] == "w" else "w"

    # Lấy các ô có thể tấn công
    attack_squares = get_piece_attacks(game_state, row, col, piece)

    for attack_row, attack_col in attack_squares:
        if 0 <= attack_row < 8 and 0 <= attack_col < 8:
            target_piece = game_state.board[attack_row][attack_col]
            if target_piece != "--" and target_piece[0] == enemy_color:
                # Bonus cho việc tấn công quân đắt tiền
                if target_piece[1] in ["Q", "R"]:
                    targets += 2
                elif target_piece[1] in ["B", "N"]:
                    targets += 1

    return targets


def is_creating_pin(game_state, move):
    """Kiểm tra nước đi có tạo ra pin không"""
    piece = move.piece_moved
    if piece[1] in ["R", "Q"]:  # Xe hoặc Hậu có thể tạo pin
        return check_line_pin(game_state, move.end_row, move.end_col, piece[0])
    elif piece[1] in ["B", "Q"]:  # Tượng hoặc Hậu có thể tạo pin chéo
        return check_diagonal_pin(game_state, move.end_row, move.end_col, piece[0])
    return False


def is_creating_skewer(game_state, move):
    """Kiểm tra nước đi có tạo ra skewer không"""
    # Simplified implementation
    return False


def is_discovered_attack(game_state, move):
    """Kiểm tra tấn công phát hiện"""
    # Simplified implementation
    return False


def check_line_pin(game_state, row, col, color):
    """Kiểm tra pin theo hàng/cột"""
    enemy_color = "b" if color == "w" else "w"
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    for dr, dc in directions:
        enemy_pieces = []
        for i in range(1, 8):
            new_row, new_col = row + dr * i, col + dc * i
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break

            piece = game_state.board[new_row][new_col]
            if piece != "--":
                if piece[0] == enemy_color:
                    enemy_pieces.append(piece)
                    if len(enemy_pieces) == 2:
                        # Có 2 quân địch trên cùng đường, có thể là pin
                        if enemy_pieces[1][1] == "K":  # Quân sau là vua
                            return True
                        break
                else:
                    break
    return False


def check_diagonal_pin(game_state, row, col, color):
    """Kiểm tra pin theo đường chéo"""
    enemy_color = "b" if color == "w" else "w"
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    for dr, dc in directions:
        enemy_pieces = []
        for i in range(1, 8):
            new_row, new_col = row + dr * i, col + dc * i
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break

            piece = game_state.board[new_row][new_col]
            if piece != "--":
                if piece[0] == enemy_color:
                    enemy_pieces.append(piece)
                    if len(enemy_pieces) == 2:
                        if enemy_pieces[1][1] == "K":
                            return True
                        break
                else:
                    break
    return False


def get_piece_attacks(game_state, row, col, piece):
    """Lấy danh sách ô mà quân có thể tấn công"""
    attacks = []
    piece_type = piece[1]

    if piece_type == "p":  # Tốt
        direction = -1 if piece[0] == "w" else 1
        for dc in [-1, 1]:
            new_row, new_col = row + direction, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                attacks.append((new_row, new_col))

    elif piece_type == "N":  # Mã
        knight_moves = [(-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2)]
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                attacks.append((new_row, new_col))

    elif piece_type == "B":  # Tượng
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                attacks.append((new_row, new_col))
                if game_state.board[new_row][new_col] != "--":
                    break

    elif piece_type == "R":  # Xe
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                attacks.append((new_row, new_col))
                if game_state.board[new_row][new_col] != "--":
                    break

    elif piece_type == "Q":  # Hậu
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                attacks.append((new_row, new_col))
                if game_state.board[new_row][new_col] != "--":
                    break

    elif piece_type == "K":  # Vua
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                attacks.append((new_row, new_col))

    return attacks


def is_square_attacked(game_state, row, col, by_color):
    """Kiểm tra ô có bị tấn công bởi màu nào đó không"""
    for r in range(8):
        for c in range(8):
            piece = game_state.board[r][c]
            if piece != "--" and piece[0] == by_color:
                attacks = get_piece_attacks(game_state, r, c, piece)
                if (row, col) in attacks:
                    return True
    return False


def get_position_key(game_state):
    """Tạo key duy nhất cho vị trí bàn cờ"""
    board_str = ""
    for row in game_state.board:
        for piece in row:
            board_str += piece + ","

    turn = "w" if game_state.white_to_move else "b"
    castle_rights = f"{game_state.current_castling_rights.wks}{game_state.current_castling_rights.wqs}{game_state.current_castling_rights.bks}{game_state.current_castling_rights.bqs}"
    en_passant = str(game_state.enpassant_possible)

    return f"{board_str}|{turn}|{castle_rights}|{en_passant}"


def is_repetition_move(position_key, game_state):
    """Kiểm tra nước đi có dẫn đến lặp lại vị trí không"""
    global position_history
    count = position_history.get(position_key, 0)
    return count >= 2


def is_winning_position(game_state):
    """Kiểm tra AI có đang thắng không"""
    current_eval = scoreBoard_advanced(game_state)
    if game_state.white_to_move:
        return current_eval > 2.0
    else:
        return current_eval < -2.0


def update_position_history(game_state):
    """Cập nhật lịch sử vị trí"""
    global position_history
    position_key = get_position_key(game_state)
    position_history[position_key] = position_history.get(position_key, 0) + 1


def clear_position_history():
    """Xóa lịch sử vị trí"""
    global position_history
    position_history = {}


# Điểm số theo giai đoạn (midgame/endgame)
piece_values = {
    "p": {"mg": 1.0, "eg": 1.3},
    "N": {"mg": 3.2, "eg": 3.3},
    "B": {"mg": 3.3, "eg": 3.4},
    "R": {"mg": 5.0, "eg": 5.1},
    "Q": {"mg": 9.0, "eg": 9.5},
    "K": {"mg": 0, "eg": 0}
}

# Bảng điểm vị trí
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
MAX_DEPTH = 5


def get_game_phase(board):
    """Tính giai đoạn trò chơi (0=khai cuộc, 1=tàn cuộc)"""
    total_material = 0
    max_material = 2 * (piece_values["Q"]["mg"] + 2 * piece_values["R"]["mg"] +
                        2 * piece_values["B"]["mg"] + 2 * piece_values["N"]["mg"])

    for row in board:
        for piece in row:
            if piece != "--" and piece[1] != "K" and piece[1] != "p":
                total_material += piece_values[piece[1]]["mg"]

    if max_material == 0:
        return 1.0

    phase = 1.0 - (total_material / max_material)
    return min(1.0, max(0.0, phase))


def get_piece_value(piece_type, game_phase):
    """Lấy giá trị quân cờ theo giai đoạn trò chơi"""
    mg_value = piece_values[piece_type]["mg"]
    eg_value = piece_values[piece_type]["eg"]
    return mg_value * (1 - game_phase) + eg_value * game_phase


def quiescence_search(game_state, alpha, beta, turn_multiplier):
    """Tìm kiếm đến khi hết nước ăn quân/chiếu tướng"""
    eval_score = turn_multiplier * scoreBoard_advanced(game_state)

    if eval_score >= beta:
        return beta
    if eval_score > alpha:
        alpha = eval_score

    # Chỉ xét nước ăn quân
    all_moves = game_state.getValidMoves()
    capture_moves = [move for move in all_moves if move.piece_captured != "--"]

    for move in capture_moves:
        game_state.makeMove(move)
        score = -quiescence_search(game_state, -beta, -alpha, -turn_multiplier)
        game_state.undoMove()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def findBestMoveIterative(game_state, valid_moves, return_queue, max_time=4):
    """Iterative Deepening với tactical improvements"""
    global best_move_found
    best_move_found = None
    start_time = time.time()

    update_position_history(game_state)

    ordered_moves = order_moves_tactical(valid_moves, game_state)

    for depth in range(1, MAX_DEPTH + 1):
        if time.time() - start_time > max_time:
            break

        score = findMoveNegaMaxAlphaBetaAdvanced(
            game_state, ordered_moves, depth, -CHECKMATE, CHECKMATE,
            1 if game_state.white_to_move else -1, depth
        )

        print(
            f"Depth {depth}: Best move = {best_move_found}, Score = {score:.2f}, Time = {time.time() - start_time:.2f}s")

        if time.time() - start_time > max_time:
            break

    return_queue.put(best_move_found if best_move_found else valid_moves[0])


def findBestMove(game_state, valid_moves, return_queue):
    """Wrapper cho compatibility với code cũ"""
    findBestMoveIterative(game_state, valid_moves, return_queue, max_time=3)


def findMoveNegaMaxAlphaBetaAdvanced(game_state, valid_moves, depth, alpha, beta, turn_multiplier, original_depth):
    global best_move_found

    if depth == 0:
        return quiescence_search(game_state, alpha, beta, turn_multiplier)

    max_score = -CHECKMATE
    best_move = None
    ordered_moves = order_moves_tactical(valid_moves, game_state)

    for move in ordered_moves:
        game_state.makeMove(move)
        next_moves = game_state.getValidMoves()
        score = -findMoveNegaMaxAlphaBetaAdvanced(
            game_state, next_moves, depth - 1, -beta, -alpha, -turn_multiplier, original_depth
        )

        if score > max_score:
            max_score = score
            if depth == original_depth:
                best_move = move
                best_move_found = move

        game_state.undoMove()

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    return max_score


def scoreBoard_advanced(game_state):
    """Hàm đánh giá nâng cao"""
    if game_state.checkmate:
        if game_state.white_to_move:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif game_state.stalemate:
        return STALEMATE

    score = 0
    game_phase = get_game_phase(game_state.board)

    for row in range(len(game_state.board)):
        for col in range(len(game_state.board[row])):
            piece = game_state.board[row][col]
            if piece != "--":
                # Điểm quân cờ theo giai đoạn
                piece_value = get_piece_value(piece[1], game_phase)

                # Điểm vị trí
                piece_position_score = 0
                if piece[1] != "K":
                    piece_position_score = piece_position_scores[piece][row][col]

                # Bonus kiểm soát trung tâm (quan trọng hơn trong khai cuộc)
                center_bonus = 0
                if (row, col) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                    center_bonus = 0.3 * (1 - game_phase)

                # Bonus phát triển quân trong khai cuộc
                development_bonus = 0
                if game_phase < 0.3:  # Chỉ trong khai cuộc
                    if piece[0] == "w" and row == 7:
                        if piece[1] in ["N", "B"] and col in [1, 2, 5, 6]:
                            development_bonus = -0.2
                    elif piece[0] == "b" and row == 0:
                        if piece[1] in ["N", "B"] and col in [1, 2, 5, 6]:
                            development_bonus = -0.2

                # Bonus an toàn vua
                king_safety_bonus = 0
                if piece[1] == "K":
                    if game_phase < 0.5:
                        if piece[0] == "w" and row == 7 and col in [2, 6]:
                            king_safety_bonus = 0.5
                        elif piece[0] == "b" and row == 0 and col in [2, 6]:
                            king_safety_bonus = 0.5

                # Bonus cấu trúc tốt (đơn giản)
                pawn_structure_bonus = 0
                if piece[1] == "p":
                    # Phạt tốt đôi
                    if has_doubled_pawn(game_state.board, col, piece[0]):
                        pawn_structure_bonus -= 0.2

                    # Thưởng tốt thông
                    if is_passed_pawn(game_state.board, row, col, piece[0]):
                        pawn_structure_bonus += 0.5 * game_phase  # Quan trọng hơn trong endgame

                total_value = (piece_value + piece_position_score + center_bonus +
                               development_bonus + king_safety_bonus + pawn_structure_bonus)

                if piece[0] == "w":
                    score += total_value
                else:
                    score -= total_value

    return score


def has_doubled_pawn(board, col, color):
    """Kiểm tra có tốt đôi trong cột không"""
    pawn_count = 0
    for row in range(8):
        if board[row][col] == f"{color}p":
            pawn_count += 1
    return pawn_count > 1


def is_passed_pawn(board, row, col, color):
    """Kiểm tra tốt có phải tốt thông không"""
    if color == "w":
        # Kiểm tra các cột liền kề phía trước có tốt đen không
        for check_col in [col - 1, col, col + 1]:
            if 0 <= check_col < 8:
                for check_row in range(row):
                    if board[check_row][check_col] == "bp":
                        return False
    else:
        # Tương tự cho tốt đen
        for check_col in [col - 1, col, col + 1]:
            if 0 <= check_col < 8:
                for check_row in range(row + 1, 8):
                    if board[check_row][check_col] == "wp":
                        return False
    return True


def findRandomMove(valid_moves):
    """Picks and returns a random valid move."""
    return random.choice(valid_moves)