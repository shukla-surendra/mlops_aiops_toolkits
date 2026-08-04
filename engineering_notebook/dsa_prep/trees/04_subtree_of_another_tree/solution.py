"""4. Subtree of Another Tree — Easy
DFS over root, using an identical-subtree check as a subroutine.
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _is_same(p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
    if not p and not q:
        return True
    if not p or not q or p.val != q.val:
        return False
    return _is_same(p.left, q.left) and _is_same(p.right, q.right)


def is_subtree(root: Optional[TreeNode], sub_root: Optional[TreeNode]) -> bool:
    if not root:
        return sub_root is None
    if _is_same(root, sub_root):
        return True
    return is_subtree(root.left, sub_root) or is_subtree(root.right, sub_root)


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(4, TreeNode(1), TreeNode(2)), TreeNode(5))
    sub = TreeNode(4, TreeNode(1), TreeNode(2))
    assert is_subtree(root, sub) is True

    root2 = TreeNode(3, TreeNode(4, TreeNode(1), TreeNode(2, TreeNode(0))), TreeNode(5))
    assert is_subtree(root2, sub) is False
    print("All tests passed.")
