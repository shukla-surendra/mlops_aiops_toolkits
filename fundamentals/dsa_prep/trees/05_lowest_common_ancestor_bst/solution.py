"""5. Lowest Common Ancestor of a BST — Medium
Iterative traversal guided by BST ordering.
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def lowest_common_ancestor(root: TreeNode, p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
    node = root
    while node:
        if p.val < node.val and q.val < node.val:
            node = node.left
        elif p.val > node.val and q.val > node.val:
            node = node.right
        else:
            return node
    return None


if __name__ == "__main__":
    n0, n3, n5 = TreeNode(0), TreeNode(3), TreeNode(5)
    n2 = TreeNode(2, n0, TreeNode(4, n3, n5))
    n7, n9 = TreeNode(7), TreeNode(9)
    n8 = TreeNode(8, n7, n9)
    root = TreeNode(6, n2, n8)

    assert lowest_common_ancestor(root, n2, n8).val == 6
    assert lowest_common_ancestor(root, n2, n2.right).val == 2
    print("All tests passed.")
