"""1. Maximum Subarray — Medium
Kadane's algorithm: greedily restart the running sum when it goes negative.
"""
from typing import List


def max_sub_array(nums: List[int]) -> int:
    best = current = nums[0]

    for num in nums[1:]:
        current = max(num, current + num)
        best = max(best, current)

    return best


if __name__ == "__main__":
    assert max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert max_sub_array([1]) == 1
    assert max_sub_array([-1, -2, -3]) == -1
    print("All tests passed.")
