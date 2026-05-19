import chess
import time
from typing import Optional, Tuple, List
import z3

def _piece_to_int(piece: Optional[chess.Piece]) -> int:
    if piece is None:
        return 0
    offset = 0 if piece.color == chess.WHITE else 6
    return piece.piece_type + offset  

# Brute-Force Solver 
def brute_force_mate_in_1(fen: str) -> Tuple[Optional[str], float]:
    board = chess.Board(fen)
    t0 = time.perf_counter()

    result: Optional[str] = None
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            result = move.uci()
            board.pop()
            break
        board.pop()

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return result, elapsed_ms


# Z3 SMT Solver
def z3_mate_in_1(fen: str) -> Tuple[Optional[str], float]:
    board = chess.Board(fen)
    t0 = time.perf_counter()

    legal: List[chess.Move] = list(board.legal_moves)
    n = len(legal)

    if n == 0:
        return None, (time.perf_counter() - t0) * 1000

    s = z3.Solver()
    move_idx = z3.Int("move_idx")
    s.add(move_idx >= 0, move_idx < n)
    pre_state = [_piece_to_int(board.piece_at(sq)) for sq in chess.SQUARES]
    post_board = [z3.Int(f"sq1_{sq}") for sq in chess.SQUARES]
    for v in post_board:
        s.add(v >= 0, v <= 12)
    mate_indices: List[int] = []
    post_snapshots: List[List[int]] = []

    for i, move in enumerate(legal):
        board.push(move)

        if board.is_checkmate():
            mate_indices.append(i)

        snapshot = [_piece_to_int(board.piece_at(sq)) for sq in chess.SQUARES]
        post_snapshots.append(snapshot)

        board.pop()

    for i, snapshot in enumerate(post_snapshots):
        board_eq = z3.And(*[post_board[sq] == snapshot[sq] for sq in chess.SQUARES])
        s.add(z3.Implies(move_idx == i, board_eq))
    if not mate_indices:
        s.add(z3.BoolVal(False))
    else:
        s.add(z3.Or(*[move_idx == i for i in mate_indices]))
    result = s.check()
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if result == z3.sat:
        idx = s.model()[move_idx].as_long()
        return legal[idx].uci(), elapsed_ms

    return None, elapsed_ms

def benchmark(puzzles: List[dict], runs: int = 1) -> List[dict]:
    results = []
    for p in puzzles:
        fen = p["fen"]
        expected = p.get("solution")

        bf_times, z3_times = [], []
        bf_move = z3_move = None

        for _ in range(runs):
            bf_move, t = brute_force_mate_in_1(fen)
            bf_times.append(t)
            z3_move, t = z3_mate_in_1(fen)
            z3_times.append(t)

        results.append({
            "name":      p["name"],
            "fen":       fen,
            "expected":  expected,
            "bf_move":   bf_move,
            "z3_move":   z3_move,
            "bf_ms":     sum(bf_times) / runs,
            "z3_ms":     sum(z3_times) / runs,
            "correct_bf": bf_move == expected,
            "correct_z3": z3_move == expected,
            "agree":     bf_move == z3_move,
        })

    return results

#list of puzzles
PUZZLES = [
    {"name": "Scholar's Mate",
     "fen":  "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
     "solution": "h5f7"},
    {"name": "Back Rank – Rook",
     "fen":  "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
     "solution": "a1a8"},
    {"name": "Anastasia's Mate",
     "fen":  "5k2/R4ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1",
     "solution": "a7a8"},
    {"name": "Two Rooks Epaulette",
     "fen":  "k7/2R5/K1R5/8/8/8/8/8 w - - 0 1",
     "solution": "c7c8"},
    {"name": "Rook Support Mate",
     "fen":  "k7/2R5/1K6/8/8/8/8/8 w - - 0 1",
     "solution": "c7c8"},
    {"name": "Arabian Mate",
     "fen":  "7k/6R1/5N2/8/8/8/8/7K w - - 0 1",
     "solution": "g7g8"},
    {"name": "Ladder Mate (Rook)",
     "fen":  "7k/8/6KR/8/8/8/8/8 w - - 0 1",
     "solution": "h6h7"}, 
    {"name": "Rook a8 – King support",
     "fen":  "5k2/R7/5K2/8/8/8/8/8 w - - 0 1",
     "solution": "a7a8"},
    {"name": "Queen + King – Corridor",
     "fen":  "k7/8/KQ6/8/8/8/8/8 w - - 0 1",
     "solution": "b6b7"},
    {"name": "Queen a7 – Support",
     "fen":  "1k6/Q7/1K6/8/8/8/8/8 w - - 0 1",
     "solution": "a7b7"},
    {"name": "Rook 8th Rank",
     "fen":  "k1K5/8/1R6/8/8/8/8/8 w - - 0 1",
     "solution": "b6a6"},
    {"name": "Queen + King – Corner",
     "fen":  "8/8/8/8/8/k7/1K6/Q7 w - - 0 1",
     "solution": "a1a3"},
    {"name": "No Mate – Open Position",
     "fen":  "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
     "solution": None},
    {"name": "No Mate – Knight Outpost",
     "fen":  "5k2/8/4N3/8/8/8/8/4K3 w - - 0 1",
     "solution": None},
]


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        fen = sys.argv[1]
        print(f"FEN: {fen}")
        bf, bt = brute_force_mate_in_1(fen)
        z3m, zt = z3_mate_in_1(fen)
        print(f"Brute-force : {bf}  ({bt:.2f} ms)")
        print(f"Z3 SMT      : {z3m}  ({zt:.2f} ms)")
        sys.exit(0)

    print(f"\n{'Puzzle':<28} {'Expected':<8} {'BF':<8} {'BF ms':>7}  {'Z3':<8} {'Z3 ms':>7}  {'✓'}")
    print("─" * 85)

    results = benchmark(PUZZLES, runs=3)
    total_correct = 0

    for r in results:
        ok = "✓" if r["agree"] else "✗"
        if r["agree"] and r["bf_move"] == r["expected"]:
            total_correct += 1
        print(
            f"{r['name']:<28} {str(r['expected']):<8} "
            f"{str(r['bf_move']):<8} {r['bf_ms']:>7.2f}  "
            f"{str(r['z3_move']):<8} {r['z3_ms']:>7.2f}  {ok}"
        )

    print("─" * 85)
    print(f"\nPuzzles with expected answer:  {sum(1 for r in results if r['expected'] is not None)}")
    print(f"Both solvers agreed:           {sum(1 for r in results if r['agree'])}/{len(results)}")
    avg_bf = sum(r['bf_ms'] for r in results) / len(results)
    avg_z3 = sum(r['z3_ms'] for r in results) / len(results)
    print(f"Avg brute-force time:          {avg_bf:.2f} ms")
    print(f"Avg Z3 time:                   {avg_z3:.2f} ms")
    print(f"Z3 overhead factor:            {avg_z3/avg_bf:.1f}×")
