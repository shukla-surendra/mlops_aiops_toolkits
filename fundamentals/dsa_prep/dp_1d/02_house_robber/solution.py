"""2. House Robber — Medium
Running max with two variables: best-including-prev vs best-excluding-prev.
"""
from typing import List


def rob(nums: List[int]) -> int:
    rob_prev, skip_prev = 0, 0

    for num in nums:
        new_rob = skip_prev + num
        skip_prev = max(skip_prev, rob_prev)
        rob_prev = new_rob

    return max(rob_prev, skip_prev)


if __name__ == "__main__":
    assert rob([1, 2, 3, 1]) == 4
    assert rob([2, 7, 9, 3, 1]) == 12
    assert rob([]) == 0
    assert rob([5]) == 5
    print("All tests passed.")
