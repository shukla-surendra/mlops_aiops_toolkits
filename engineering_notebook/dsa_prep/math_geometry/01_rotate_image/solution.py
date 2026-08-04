"""1. Rotate Image — Medium
Transpose the matrix, then reverse each row, all in place.
"""
from typing import List


def rotate(matrix: List[List[int]]) -> None:
    n = len(matrix)

    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    for row in matrix:
        row.reverse()


if __name__ == "__main__":
    m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    rotate(m)
    assert m == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]

    m2 = [[1]]
    rotate(m2)
    assert m2 == [[1]]
    print("All tests passed.")
