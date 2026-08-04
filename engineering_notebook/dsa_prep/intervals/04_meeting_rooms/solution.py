"""4. Meeting Rooms — Easy
Sort by start time; a conflict can only occur between adjacent intervals.
"""
from typing import List


def can_attend_meetings(intervals: List[List[int]]) -> bool:
    intervals.sort(key=lambda pair: pair[0])

    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i - 1][1]:
            return False

    return True


if __name__ == "__main__":
    assert can_attend_meetings([[0, 30], [5, 10], [15, 20]]) is False
    assert can_attend_meetings([[7, 10], [2, 4]]) is True
    assert can_attend_meetings([]) is True
    print("All tests passed.")
