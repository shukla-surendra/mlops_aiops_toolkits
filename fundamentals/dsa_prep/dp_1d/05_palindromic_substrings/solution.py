"""5. Palindromic Substrings — Medium
Expand around every center, counting each valid expansion.
"""


def count_substrings(s: str) -> int:
    count = 0

    def expand(left, right):
        nonlocal count
        while left >= 0 and right < len(s) and s[left] == s[right]:
            count += 1
            left -= 1
            right += 1

    for i in range(len(s)):
        expand(i, i)
        expand(i, i + 1)

    return count


if __name__ == "__main__":
    assert count_substrings("abc") == 3
    assert count_substrings("aaa") == 6
    assert count_substrings("") == 0
    print("All tests passed.")
