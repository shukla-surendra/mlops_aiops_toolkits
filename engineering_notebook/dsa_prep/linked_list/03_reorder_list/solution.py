"""3. Reorder List — Medium
Find middle (slow/fast) -> reverse second half -> merge alternately.
"""
from typing import Optional, List


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reorder_list(head: Optional[ListNode]) -> None:
    if not head or not head.next:
        return

    slow, fast = head, head
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next

    second = slow.next
    slow.next = None
    prev = None
    while second:
        next_node = second.next
        second.next = prev
        prev = second
        second = next_node
    second = prev

    first = head
    while second:
        first_next = first.next
        second_next = second.next
        first.next = second
        second.next = first_next
        first = first_next
        second = second_next


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
    l1 = build_list([1, 2, 3, 4])
    reorder_list(l1)
    assert to_list(l1) == [1, 4, 2, 3]

    l2 = build_list([1, 2, 3, 4, 5])
    reorder_list(l2)
    assert to_list(l2) == [1, 5, 2, 4, 3]
    print("All tests passed.")
