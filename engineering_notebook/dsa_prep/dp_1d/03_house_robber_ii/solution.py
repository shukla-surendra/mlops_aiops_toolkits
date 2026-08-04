"""3. House Robber II — Medium
Reduce the circular problem to two linear House Robber subproblems.
"""
from typing import List


def _rob_linear(nums: List[int]) -> int:
    rob_prev, skip_prev = 0, 0
    for num in nums:
        new_rob = skip_prev + num
        skip_prev = max(skip_prev, rob_prev)
        rob_prev = new_rob
    return max(rob_prev, skip_prev)


def rob(nums: List[int]) -> int:
    if len(nums) == 1:
        return nums[0]

    return max(_rob_linear(nums[:-1]), _rob_linear(nums[1:]))


if __name__ == "__main__":
    assert rob([2, 3, 2]) == 3
    assert rob([1, 2, 3, 1]) == 4
    assert rob([1]) == 1
    assert rob([1, 2]) == 2
    print("All tests passed.")
