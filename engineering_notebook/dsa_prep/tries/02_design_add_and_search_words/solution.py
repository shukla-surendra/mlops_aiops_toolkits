"""2. Design Add and Search Words Data Structure — Medium
Trie insert + DFS/backtracking search to handle '.' wildcards.
"""


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False


class WordDictionary:
    def __init__(self):
        self.root = TrieNode()

    def add_word(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def search(self, word: str) -> bool:
        def dfs(node: TrieNode, i: int) -> bool:
            if i == len(word):
                return node.is_end

            ch = word[i]
            if ch == ".":
                return any(dfs(child, i + 1) for child in node.children.values())

            child = node.children.get(ch)
            return child is not None and dfs(child, i + 1)

        return dfs(self.root, 0)


if __name__ == "__main__":
    wd = WordDictionary()
    wd.add_word("bad")
    wd.add_word("dad")
    wd.add_word("mad")
    assert wd.search("pad") is False
    assert wd.search("bad") is True
    assert wd.search(".ad") is True
    assert wd.search("b..") is True
    print("All tests passed.")
