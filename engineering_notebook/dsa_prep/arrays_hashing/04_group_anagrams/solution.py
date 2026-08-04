"""4. Group Anagrams — Medium
Bucket strings by a canonical 26-letter count signature.
"""
from typing import List
from collections import defaultdict


def group_anagrams(strs: List[str]) -> List[List[str]]:
    buckets = defaultdict(list)
    for word in strs:
        counts = [0] * 26
        for ch in word:
            counts[ord(ch) - ord("a")] += 1
        buckets[tuple(counts)].append(word)
    return list(buckets.values())


if __name__ == "__main__":
    result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    groups = {frozenset(g) for g in result}
    expected = {frozenset(["bat"]), frozenset(["nat", "tan"]), frozenset(["ate", "eat", "tea"])}
    assert groups == expected
    assert group_anagrams([""]) == [[""]]
    print("All tests passed.")
