"""4. 0/1 Knapsack — Medium
Bounded knapsack DP; each item may be used at most once.
"""
from typing import List


def knapsack(weights: List[int], values: List[int], capacity: int) -> int:
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        weight, value = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if weight <= w:
                dp[i][w] = max(dp[i][w], value + dp[i - 1][w - weight])

    return dp[n][capacity]


if __name__ == "__main__":
    assert knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7) == 9
    assert knapsack([1, 2, 3], [6, 10, 12], 5) == 22
    assert knapsack([], [], 10) == 0
    print("All tests passed.")
