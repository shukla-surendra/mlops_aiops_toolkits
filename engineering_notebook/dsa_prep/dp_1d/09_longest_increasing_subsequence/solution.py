"""9. Longest Increasing Subsequence — Medium
Patience-sorting approach: maintain smallest tail per subsequence length, O(n log n).
"""
import bisect
from typing import List


def length_of_lis(nums: List[int]) -> int:
    tails: List[int] = []

    for num in nums:
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num

    return len(tails)


if __name__ == "__main__":
    assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4
    assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4
    assert length_of_lis([7, 7, 7, 7]) == 1
    assert length_of_lis([]) == 0
    print("All tests passed.")
