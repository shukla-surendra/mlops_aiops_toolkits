"""4. Hand of Straights — Medium
Min-heap of distinct values, greedily consuming groupSize-length runs from the smallest.
"""
import heapq
from typing import List
from collections import Counter


def is_n_straight_hand(hand: List[int], group_size: int) -> bool:
    if len(hand) % group_size != 0:
        return False

    counts = Counter(hand)
    min_heap = list(counts.keys())
    heapq.heapify(min_heap)

    while min_heap:
        smallest = min_heap[0]
        if counts[smallest] == 0:
            heapq.heappop(min_heap)
            continue

        for card in range(smallest, smallest + group_size):
            if counts[card] == 0:
                return False
            counts[card] -= 1

    return True


if __name__ == "__main__":
    assert is_n_straight_hand([1, 2, 3, 6, 2, 3, 4, 7, 8], 3) is True
    assert is_n_straight_hand([1, 2, 3, 4, 5], 4) is False
    assert is_n_straight_hand([], 1) is True
    print("All tests passed.")
