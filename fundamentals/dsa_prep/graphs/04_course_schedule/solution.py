"""4. Course Schedule — Medium
DFS cycle detection using a visiting/visited state per node.
"""
from typing import List
from collections import defaultdict


def can_finish(num_courses: int, prerequisites: List[List[int]]) -> bool:
    graph = defaultdict(list)
    for course, prereq in prerequisites:
        graph[course].append(prereq)

    visiting = set()
    visited = set()

    def has_cycle(course):
        if course in visited:
            return False
        if course in visiting:
            return True

        visiting.add(course)
        for prereq in graph[course]:
            if has_cycle(prereq):
                return True
        visiting.remove(course)
        visited.add(course)

        return False

    for course in range(num_courses):
        if has_cycle(course):
            return False

    return True


if __name__ == "__main__":
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    assert can_finish(1, []) is True
    print("All tests passed.")
