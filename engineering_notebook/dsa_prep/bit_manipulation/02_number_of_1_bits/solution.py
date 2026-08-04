"""2. Number of 1 Bits — Easy
Brian Kernighan's trick: n & (n-1) clears the lowest set bit each iteration.
"""


def hamming_weight(n: int) -> int:
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


if __name__ == "__main__":
    assert hamming_weight(0b1011) == 3
    assert hamming_weight(0b10000000) == 1
    assert hamming_weight(0) == 0
    print("All tests passed.")
