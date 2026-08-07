"""1. Unique Paths — Medium
Grid DP with a rolling 1-D row array.
"""


def unique_paths(m: int, n: int) -> int:
    row = [1] * n

    for _ in range(1, m):
        for c in range(1, n):
            row[c] += row[c - 1]

    return row[-1]


if __name__ == "__main__":
    assert unique_paths(3, 7) == 28
    assert unique_paths(3, 2) == 3
    assert unique_paths(1, 1) == 1
    print("All tests passed.")
