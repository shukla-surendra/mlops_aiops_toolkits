"""2. Jump Game — Medium
Greedy scan tracking the farthest index reachable so far.
"""
from typing import List


def can_jump(nums: List[int]) -> bool:
    farthest = 0

    for i, jump in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + jump)

    return True


if __name__ == "__main__":
    assert can_jump([2, 3, 1, 1, 4]) is True
    assert can_jump([3, 2, 1, 0, 4]) is False
    assert can_jump([0]) is True
    print("All tests passed.")
