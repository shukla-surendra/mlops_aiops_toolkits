"""3. Non-overlapping Intervals — Medium
Sort by end time; greedy activity-selection to maximize kept intervals.
"""
from typing import List


def erase_overlap_intervals(intervals: List[List[int]]) -> int:
    intervals.sort(key=lambda pair: pair[1])

    removed = 0
    prev_end = float("-inf")

    for start, end in intervals:
        if start >= prev_end:
            prev_end = end
        else:
            removed += 1

    return removed


if __name__ == "__main__":
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0
    print("All tests passed.")
