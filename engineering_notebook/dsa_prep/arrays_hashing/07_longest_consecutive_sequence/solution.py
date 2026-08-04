"""7. Longest Consecutive Sequence — Medium
Hash set + only expand runs from their start element for amortized O(n).
"""
from typing import List


def longest_consecutive(nums: List[int]) -> int:
    num_set = set(nums)
    longest = 0

    for num in num_set:
        if num - 1 not in num_set:
            length = 1
            while num + length in num_set:
                length += 1
            longest = max(longest, length)

    return longest


if __name__ == "__main__":
    assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4
    assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9
    assert longest_consecutive([]) == 0
    print("All tests passed.")
