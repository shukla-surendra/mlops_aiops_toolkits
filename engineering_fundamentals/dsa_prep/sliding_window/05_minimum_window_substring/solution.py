"""5. Minimum Window Substring — Hard
Grow-to-valid, shrink-to-minimize sliding window with a have/need counter.
"""
from collections import Counter


def min_window(s: str, t: str) -> str:
    if not s or not t:
        return ""

    need = Counter(t)
    required = len(need)

    window = {}
    have = 0
    left = 0
    best_len = float("inf")
    best_left = 0

    for right, ch in enumerate(s):
        window[ch] = window.get(ch, 0) + 1
        if ch in need and window[ch] == need[ch]:
            have += 1

        while have == required:
            if right - left + 1 < best_len:
                best_len = right - left + 1
                best_left = left

            left_ch = s[left]
            window[left_ch] -= 1
            if left_ch in need and window[left_ch] < need[left_ch]:
                have -= 1
            left += 1

    return "" if best_len == float("inf") else s[best_left:best_left + best_len]


if __name__ == "__main__":
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "aa") == ""
    assert min_window("a", "a") == "a"
    print("All tests passed.")
