"""5. Meeting Rooms II — Medium
Min-heap of active meeting end times, tracking the max concurrently in use.
"""
import heapq
from typing import List


def min_meeting_rooms(intervals: List[List[int]]) -> int:
    if not intervals:
        return 0

    intervals.sort(key=lambda pair: pair[0])
    heap = []  # end times of meetings currently in progress

    for start, end in intervals:
        if heap and heap[0] <= start:
            heapq.heappop(heap)
        heapq.heappush(heap, end)

    return len(heap)


if __name__ == "__main__":
    assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_meeting_rooms([[7, 10], [2, 4]]) == 1
    assert min_meeting_rooms([]) == 0
    print("All tests passed.")
