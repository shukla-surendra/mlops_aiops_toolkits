"""3. Permutations — Medium
Backtracking with a used-tracker to build each permutation one slot at a time.
"""
from typing import List


def permute(nums: List[int]) -> List[List[int]]:
    result = []
    path = []
    used = [False] * len(nums)

    def backtrack():
        if len(path) == len(nums):
            result.append(path[:])
            return

        for i, num in enumerate(nums):
            if used[i]:
                continue
            used[i] = True
            path.append(num)
            backtrack()
            path.pop()
            used[i] = False

    backtrack()
    return result


if __name__ == "__main__":
    result = {tuple(p) for p in permute([1, 2, 3])}
    expected = {(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1)}
    assert result == expected
    assert permute([1]) == [[1]]
    print("All tests passed.")
