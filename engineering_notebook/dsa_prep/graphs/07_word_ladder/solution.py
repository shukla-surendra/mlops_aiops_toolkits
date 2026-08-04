"""7. Word Ladder — Hard
BFS shortest path using wildcard patterns for fast neighbor lookup.
"""
from typing import List
from collections import defaultdict, deque


def ladder_length(begin_word: str, end_word: str, word_list: List[str]) -> int:
    words = set(word_list)
    if end_word not in words:
        return 0

    L = len(begin_word)
    patterns = defaultdict(list)
    for word in words:
        for i in range(L):
            pattern = word[:i] + "*" + word[i + 1:]
            patterns[pattern].append(word)

    visited = {begin_word}
    queue = deque([(begin_word, 1)])

    while queue:
        word, steps = queue.popleft()
        if word == end_word:
            return steps

        for i in range(L):
            pattern = word[:i] + "*" + word[i + 1:]
            for neighbor in patterns[pattern]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, steps + 1))

    return 0


if __name__ == "__main__":
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]) == 5
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log"]) == 0
    print("All tests passed.")
