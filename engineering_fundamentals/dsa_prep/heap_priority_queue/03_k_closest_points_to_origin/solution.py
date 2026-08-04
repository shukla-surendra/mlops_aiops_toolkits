"""3. K Closest Points to Origin — Medium
Max-heap of size k keyed by squared distance (negated for Python's min-heap).
"""
import heapq
from typing import List


def k_closest(points: List[List[int]], k: int) -> List[List[int]]:
    heap = []

    for x, y in points:
        dist = x * x + y * y
        heapq.heappush(heap, (-dist, x, y))
        if len(heap) > k:
            heapq.heappop(heap)

    return [[x, y] for _, x, y in heap]


if __name__ == "__main__":
    result = k_closest([[1, 3], [-2, 2]], 1)
    assert result == [[-2, 2]]

    result2 = {tuple(p) for p in k_closest([[3, 3], [5, -1], [-2, 4]], 2)}
    assert result2 == {(3, 3), (-2, 4)}
    print("All tests passed.")
