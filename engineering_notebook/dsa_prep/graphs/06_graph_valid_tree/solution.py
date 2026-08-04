"""6. Graph Valid Tree — Medium
Union-Find: no cycle formed while unioning + exactly one component at the end.
"""
from typing import List


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return False  # would create a cycle
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]
        self.count -= 1
        return True


def valid_tree(n: int, edges: List[List[int]]) -> bool:
    if len(edges) != n - 1:
        return False

    uf = UnionFind(n)
    for a, b in edges:
        if not uf.union(a, b):
            return False

    return uf.count == 1


if __name__ == "__main__":
    assert valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]) is True
    assert valid_tree(5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]) is False
    assert valid_tree(1, []) is True
    print("All tests passed.")
