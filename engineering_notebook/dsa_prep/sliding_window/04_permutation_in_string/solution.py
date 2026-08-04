"""4. Permutation in String — Medium
Fixed-size sliding window comparing 26-letter frequency counts.
"""


def check_inclusion(s1: str, s2: str) -> bool:
    n1, n2 = len(s1), len(s2)
    if n1 > n2:
        return False

    need = [0] * 26
    window = [0] * 26

    for ch in s1:
        need[ord(ch) - ord("a")] += 1

    for i in range(n2):
        window[ord(s2[i]) - ord("a")] += 1

        if i >= n1:
            left_ch = s2[i - n1]
            window[ord(left_ch) - ord("a")] -= 1

        if i >= n1 - 1 and window == need:
            return True

    return False


if __name__ == "__main__":
    assert check_inclusion("ab", "eidbaooo") is True
    assert check_inclusion("ab", "eidboaoo") is False
    assert check_inclusion("adc", "dcda") is True
    print("All tests passed.")
