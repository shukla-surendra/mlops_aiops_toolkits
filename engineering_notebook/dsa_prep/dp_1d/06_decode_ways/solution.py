"""6. Decode Ways — Medium
Bottom-up Fibonacci-style DP gated by single/double-digit validity.
"""


def num_decodings(s: str) -> int:
    if not s or s[0] == "0":
        return 0

    n = len(s)
    # ways_after_i means the number of ways to decode s[i:]
    ways_after = 1  # ways to decode s[n:] (empty suffix)
    ways_at = 1 if s[n - 1] != "0" else 0  # ways to decode s[n-1:]

    for i in range(n - 2, -1, -1):
        current = 0
        if s[i] != "0":
            current += ways_at
        two_digit = int(s[i:i + 2])
        if 10 <= two_digit <= 26:
            current += ways_after
        ways_after, ways_at = ways_at, current

    return ways_at


if __name__ == "__main__":
    assert num_decodings("12") == 2
    assert num_decodings("226") == 3
    assert num_decodings("06") == 0
    assert num_decodings("0") == 0
    assert num_decodings("10") == 1
    assert num_decodings("100") == 0
    print("All tests passed.")
