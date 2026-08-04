"""9. Binary Tree Maximum Path Sum — Hard
Post-order DFS returning the best one-sided downward gain, tracking a global peak sum.
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def max_path_sum(root: Optional[TreeNode]) -> int:
    best = float("-inf")

    def max_gain(node):
        nonlocal best
        if not node:
            return 0

        left_gain = max(max_gain(node.left), 0)
        right_gain = max(max_gain(node.right), 0)

        best = max(best, node.val + left_gain + right_gain)

        return node.val + max(left_gain, right_gain)

    max_gain(root)
    return best


if __name__ == "__main__":
    assert max_path_sum(TreeNode(1, TreeNode(2), TreeNode(3))) == 6
    assert max_path_sum(TreeNode(-10, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))) == 42
    assert max_path_sum(TreeNode(-3)) == -3
    print("All tests passed.")
