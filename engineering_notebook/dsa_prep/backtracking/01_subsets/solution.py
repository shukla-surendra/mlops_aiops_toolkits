"""1. Subsets — Medium
Include/exclude backtracking; every recursive call is a valid subset.
"""
from typing import List


def subsets(nums: List[int]) -> List[List[int]]:
    result = []
    path = []

    def backtrack(i):
        if i == len(nums):
            result.append(path[:])
            return

        path.append(nums[i])
        backtrack(i + 1)
        path.pop()

        backtrack(i + 1)

    backtrack(0)
    return result


if __name__ == "__main__":
    result = {tuple(sorted(s)) for s in subsets([1, 2, 3])}
    expected = {(), (1,), (2,), (1, 2), (3,), (1, 3), (2, 3), (1, 2, 3)}
    assert result == expected
    assert subsets([]) == [[]]
    print("All tests passed.")
