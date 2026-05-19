# Chess-SAT-Solver
Solves chess mate-in-1 puzzles using both a brute-force baseline and a Z3 SMT constraint solver. Compares their runtime and correctness.

# Usage
You need Python 3.8 or higher.
Then run: 
```
pip install z3-solver python-chess
```
To run the benchmark on all built-in puzzles:

```
python mate_solver.py
```
 
To solve a specific position by passing a FEN string:
 
```
python mate_solver.py "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
```
# Output
 
The benchmark prints a table showing the mating move found, time in milliseconds, and whether both solvers agreed, for each puzzle. The single-FEN mode prints the result from each solver side by side.
