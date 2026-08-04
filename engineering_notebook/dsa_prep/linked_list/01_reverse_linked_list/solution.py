"""1. Reverse Linked List — Easy
Iterative pointer reversal, O(1) space.
"""
from typing import Optional, List


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    prev = None
    curr = head

    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node

    return prev


def build_list(values: List[int]) -> Optional[ListNode]:
    dummy = ListNode()
    tail = dummy
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head: Optional[ListNode]) -> List[int]:
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result


if __name__ == "__main__":
    assert to_list(reverse_list(build_list([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert to_list(reverse_list(build_list([]))) == []
    assert to_list(reverse_list(build_list([1]))) == [1]
    print("All tests passed.")
