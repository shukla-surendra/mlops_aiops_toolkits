"""8. Word Break — Medium
Bottom-up DP: dp[i] = can s[:i] be segmented using dictionary words.
"""
from typing import List


def word_break(s: str, word_dict: List[str]) -> bool:
    words = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break

    return dp[n]


if __name__ == "__main__":
    assert word_break("leetcode", ["leet", "code"]) is True
    assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False
    assert word_break("applepenapple", ["apple", "pen"]) is True
    print("All tests passed.")
