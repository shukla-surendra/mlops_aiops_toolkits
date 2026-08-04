"""3. Pacific Atlantic Water Flow — Medium
Reverse multi-source DFS from each ocean's border cells.
"""
from typing import List


def pacific_atlantic(heights: List[List[int]]) -> List[List[int]]:
    if not heights:
        return []

    rows, cols = len(heights), len(heights[0])
    pacific, atlantic = set(), set()

    def dfs(r, c, visited, prev_height):
        if (
            r < 0 or r >= rows or c < 0 or c >= cols
            or (r, c) in visited
            or heights[r][c] < prev_height
        ):
            return
        visited.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            dfs(r + dr, c + dc, visited, heights[r][c])

    for c in range(cols):
        dfs(0, c, pacific, heights[0][c])
        dfs(rows - 1, c, atlantic, heights[rows - 1][c])
    for r in range(rows):
        dfs(r, 0, pacific, heights[r][0])
        dfs(r, cols - 1, atlantic, heights[r][cols - 1])

    return [list(cell) for cell in pacific & atlantic]


if __name__ == "__main__":
    heights = [
        [1, 2, 2, 3, 5],
        [3, 2, 3, 4, 4],
        [2, 4, 5, 3, 1],
        [6, 7, 1, 4, 5],
        [5, 1, 1, 2, 4],
    ]
    result = {tuple(cell) for cell in pacific_atlantic(heights)}
    expected = {(0, 4), (1, 3), (1, 4), (2, 2), (3, 0), (3, 1), (4, 0)}
    assert result == expected
    print("All tests passed.")
