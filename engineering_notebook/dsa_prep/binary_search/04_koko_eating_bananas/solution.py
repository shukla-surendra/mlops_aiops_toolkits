"""4. Koko Eating Bananas — Medium
Binary search over the answer (eating speed k), using a monotonic feasibility check.
"""
import math
from typing import List


def min_eating_speed(piles: List[int], h: int) -> int:
    def hours_needed(k: int) -> int:
        return sum(math.ceil(pile / k) for pile in piles)

    left, right = 1, max(piles)

    while left < right:
        mid = (left + right) // 2
        if hours_needed(mid) <= h:
            right = mid
        else:
            left = mid + 1

    return left


if __name__ == "__main__":
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23
    print("All tests passed.")
