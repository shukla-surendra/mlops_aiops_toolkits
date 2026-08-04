"""3. Same Tree — Easy
Recursive structural + value comparison.
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def is_same_tree(p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
    if not p and not q:
        return True
    if not p or not q or p.val != q.val:
        return False
    return is_same_tree(p.left, q.left) and is_same_tree(p.right, q.right)


if __name__ == "__main__":
    assert is_same_tree(TreeNode(1, TreeNode(2), TreeNode(3)), TreeNode(1, TreeNode(2), TreeNode(3))) is True
    assert is_same_tree(TreeNode(1, TreeNode(2)), TreeNode(1, None, TreeNode(2))) is False
    assert is_same_tree(None, None) is True
    print("All tests passed.")
