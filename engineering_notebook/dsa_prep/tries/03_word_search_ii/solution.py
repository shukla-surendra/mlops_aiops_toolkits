"""3. Word Search II — Hard
Build a trie of all target words, then DFS the grid once, pruned by the trie.
"""
from typing import List


class TrieNode:
    def __init__(self):
        self.children = {}
        self.word = None  # set to the full word at terminal nodes


def find_words(board: List[List[str]], words: List[str]) -> List[str]:
    root = TrieNode()
    for word in words:
        node = root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.word = word

    rows, cols = len(board), len(board[0])
    result = []

    def dfs(r, c, node):
        ch = board[r][c]
        child = node.children.get(ch)
        if not child:
            return

        if child.word:
            result.append(child.word)
            child.word = None  # avoid duplicate results

        board[r][c] = "#"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                dfs(nr, nc, child)
        board[r][c] = ch

        if not child.children:
            node.children.pop(ch, None)

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)

    return result


if __name__ == "__main__":
    board = [
        ["o", "a", "a", "n"],
        ["e", "t", "a", "e"],
        ["i", "h", "k", "r"],
        ["i", "f", "l", "v"],
    ]
    words = ["oath", "pea", "eat", "rain"]
    assert set(find_words(board, words)) == {"eat", "oath"}
    print("All tests passed.")
