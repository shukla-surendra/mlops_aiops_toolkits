"""5. Linked List Cycle — Easy
Floyd's slow/fast pointer cycle detection, O(1) space.
"""
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def has_cycle(head: Optional[ListNode]) -> bool:
    slow = fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True

    return False


if __name__ == "__main__":
    a, b, c, d = ListNode(3), ListNode(2), ListNode(0), ListNode(-4)
    a.next, b.next, c.next, d.next = b, c, d, b  # cycle back to b
    assert has_cycle(a) is True

    x, y = ListNode(1), ListNode(2)
    x.next = y
    assert has_cycle(x) is False
    assert has_cycle(None) is False
    print("All tests passed.")
