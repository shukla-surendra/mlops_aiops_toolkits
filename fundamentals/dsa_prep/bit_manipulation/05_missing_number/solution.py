"""5. Missing Number — Easy
XOR every index and value together; only the missing number survives unpaired.
"""
from typing import List


def missing_number(nums: List[int]) -> int:
    result = len(nums)
    for i, num in enumerate(nums):
        result ^= i ^ num
    return result


if __name__ == "__main__":
    assert missing_number([3, 0, 1]) == 2
    assert missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8
    assert missing_number([0]) == 1
    print("All tests passed.")
