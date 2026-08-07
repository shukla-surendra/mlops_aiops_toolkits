"""1. Best Time to Buy and Sell Stock — Easy
Track running minimum price and best profit seen so far, in one pass.
"""
from typing import List


def max_profit(prices: List[int]) -> int:
    min_price = float("inf")
    best_profit = 0

    for price in prices:
        min_price = min(min_price, price)
        best_profit = max(best_profit, price - min_price)

    return best_profit


if __name__ == "__main__":
    assert max_profit([7, 1, 5, 3, 6, 4]) == 5
    assert max_profit([7, 6, 4, 3, 1]) == 0
    assert max_profit([]) == 0
    print("All tests passed.")
