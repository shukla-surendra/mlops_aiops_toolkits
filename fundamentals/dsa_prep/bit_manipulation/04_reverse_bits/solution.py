"""4. Reverse Bits — Easy
Extract n's bits lowest-to-highest, appending each into the result.
"""


def reverse_bits(n: int) -> int:
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result


if __name__ == "__main__":
    assert reverse_bits(0b00000010100101000001111010011100) == 0b00111001011110000010100101000000
    assert reverse_bits(0b11111111111111111111111111111101) == 0b10111111111111111111111111111111
    print("All tests passed.")
