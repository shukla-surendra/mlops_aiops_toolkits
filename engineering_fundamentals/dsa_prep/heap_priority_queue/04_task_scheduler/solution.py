"""4. Task Scheduler — Medium
Closed-form chunking based on the most frequent task's count.
"""
from typing import List
from collections import Counter


def least_interval(tasks: List[str], n: int) -> int:
    counts = Counter(tasks)
    max_freq = max(counts.values())
    max_count = sum(1 for c in counts.values() if c == max_freq)

    chunks_len = (max_freq - 1) * (n + 1) + max_count
    return max(chunks_len, len(tasks))


if __name__ == "__main__":
    assert least_interval(["A", "A", "A", "B", "B", "B"], 2) == 8
    assert least_interval(["A", "A", "A", "B", "B", "B"], 0) == 6
    assert least_interval(["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2) == 16
    print("All tests passed.")
