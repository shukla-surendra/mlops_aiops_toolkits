"""4. Daily Temperatures — Medium
Monotonic decreasing stack of indices; amortized O(n).
"""
from typing import List


def daily_temperatures(temperatures: List[int]) -> List[int]:
    answer = [0] * len(temperatures)
    stack = []  # indices with decreasing temperatures

    for i, temp in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temp:
            prev_index = stack.pop()
            answer[prev_index] = i - prev_index
        stack.append(i)

    return answer


if __name__ == "__main__":
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert daily_temperatures([30, 60, 90]) == [1, 1, 0]
    print("All tests passed.")
