"""2. Combination Sum — Medium
Backtracking; staying at the same index allows unlimited reuse of a candidate.
"""
from typing import List


def combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    result = []
    path = []

    def backtrack(i, remaining):
        if remaining == 0:
            result.append(path[:])
            return
        if remaining < 0 or i == len(candidates):
            return

        path.append(candidates[i])
        backtrack(i, remaining - candidates[i])
        path.pop()

        backtrack(i + 1, remaining)

    backtrack(0, target)
    return result


if __name__ == "__main__":
    def normalize(combos):
        return sorted(sorted(c) for c in combos)

    assert normalize(combination_sum([2, 3, 6, 7], 7)) == normalize([[2, 2, 3], [7]])
    assert normalize(combination_sum([2, 3, 5], 8)) == normalize([[2, 2, 2, 2], [2, 3, 3], [3, 5]])
    print("All tests passed.")
