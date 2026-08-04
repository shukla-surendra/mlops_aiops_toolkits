"""7. Validate Binary Search Tree — Medium
DFS propagating a (low, high) valid-range bound down the tree.
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def is_valid_bst(root: Optional[TreeNode]) -> bool:
    def valid(node, low, high):
        if not node:
            return True
        if not (low < node.val < high):
            return False
        return valid(node.left, low, node.val) and valid(node.right, node.val, high)

    return valid(root, float("-inf"), float("inf"))


if __name__ == "__main__":
    assert is_valid_bst(TreeNode(2, TreeNode(1), TreeNode(3))) is True
    assert is_valid_bst(TreeNode(5, TreeNode(1), TreeNode(4, TreeNode(3), TreeNode(6)))) is False
    assert is_valid_bst(None) is True
    print("All tests passed.")
