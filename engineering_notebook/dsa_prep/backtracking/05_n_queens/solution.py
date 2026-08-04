"""5. N-Queens — Hard
Row-by-row backtracking with O(1) column/diagonal conflict tracking via sets.
"""
from typing import List


def solve_n_queens(n: int) -> List[List[str]]:
    result = []
    cols = set()
    diag1 = set()  # row - col
    diag2 = set()  # row + col
    board = [["."] * n for _ in range(n)]

    def backtrack(row):
        if row == n:
            result.append(["".join(r) for r in board])
            return

        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue

            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            board[row][col] = "Q"

            backtrack(row + 1)

            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
            board[row][col] = "."

    backtrack(0)
    return result


if __name__ == "__main__":
    solutions = solve_n_queens(4)
    assert len(solutions) == 2
    assert set(map(tuple, solutions)) == {
        (".Q..", "...Q", "Q...", "..Q."),
        ("..Q.", "Q...", "...Q", ".Q.."),
    }
    assert len(solve_n_queens(1)) == 1
    assert len(solve_n_queens(2)) == 0
    print("All tests passed.")
