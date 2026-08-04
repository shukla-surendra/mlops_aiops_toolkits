"""1. Single Number — Easy
XOR every element; paired values cancel out, leaving the unpaired one.
"""
from typing import List
from functools import reduce
from operator import xor


def single_number(nums: List[int]) -> int:
    return reduce(xor, nums, 0)


if __name__ == "__main__":
    assert single_number([2, 2, 1]) == 1
    assert single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([1]) == 1
    print("All tests passed.")
