"""7. Coin Change — Medium
Bottom-up unbounded-knapsack DP over amounts 0..target.
"""
from typing import List


def coin_change(coins: List[int], amount: int) -> int:
    dp = [0] + [float("inf")] * amount

    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)

    return dp[amount] if dp[amount] != float("inf") else -1


if __name__ == "__main__":
    assert coin_change([1, 2, 5], 11) == 3
    assert coin_change([2], 3) == -1
    assert coin_change([1], 0) == 0
    print("All tests passed.")
