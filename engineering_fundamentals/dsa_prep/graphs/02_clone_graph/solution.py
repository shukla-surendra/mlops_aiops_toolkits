"""2. Clone Graph — Medium
DFS with a visited-map of original node -> clone, to handle cycles.
"""
from typing import Optional


class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def clone_graph(node: Optional["Node"]) -> Optional["Node"]:
    if not node:
        return None

    cloned = {}

    def dfs(n):
        if n in cloned:
            return cloned[n]

        copy = Node(n.val)
        cloned[n] = copy
        for neighbor in n.neighbors:
            copy.neighbors.append(dfs(neighbor))

        return copy

    return dfs(node)


if __name__ == "__main__":
    n1, n2, n3, n4 = Node(1), Node(2), Node(3), Node(4)
    n1.neighbors = [n2, n4]
    n2.neighbors = [n1, n3]
    n3.neighbors = [n2, n4]
    n4.neighbors = [n1, n3]

    clone = clone_graph(n1)
    assert clone is not n1
    assert clone.val == 1
    assert sorted(neigh.val for neigh in clone.neighbors) == [2, 4]
    assert clone_graph(None) is None
    print("All tests passed.")
