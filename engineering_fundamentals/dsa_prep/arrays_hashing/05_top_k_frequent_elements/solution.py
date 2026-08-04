"""5. Top K Frequent Elements — Medium
Counting + bucket sort by frequency for O(n).
"""
from typing import List
from collections import Counter


def top_k_frequent(nums: List[int], k: int) -> List[int]:
    counts = Counter(nums)
    buckets: List[List[int]] = [[] for _ in range(len(nums) + 1)]
    for value, freq in counts.items():
        buckets[freq].append(value)

    result = []
    for freq in range(len(buckets) - 1, 0, -1):
        for value in buckets[freq]:
            result.append(value)
            if len(result) == k:
                return result
    return result


if __name__ == "__main__":
    assert set(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == {1, 2}
    assert top_k_frequent([1], 1) == [1]
    assert set(top_k_frequent([4, 1, 1, 2, 2, 3], 2)) == {1, 2}
    print("All tests passed.")
