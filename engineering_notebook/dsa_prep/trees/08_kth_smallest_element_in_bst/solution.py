"""8. Kth Smallest Element in a BST — Medium
Iterative in-order traversal, stopping at the k-th visited node.
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    stack = []
    node = root

    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right

    raise ValueError("k is out of range for this tree")


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(1, None, TreeNode(2)), TreeNode(4))
    assert kth_smallest(root, 1) == 1

    root2 = TreeNode(5, TreeNode(3, TreeNode(2, TreeNode(1)), TreeNode(4)), TreeNode(6))
    assert kth_smallest(root2, 3) == 3
    print("All tests passed.")
