"""2. 3Sum — Medium
Sort, fix one element, two pointers for the rest — with duplicate skipping.
"""
from typing import List


def three_sum(nums: List[int]) -> List[List[int]]:
    nums.sort()
    n = len(nums)
    result = []

    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        if nums[i] > 0:
            break

        left, right = i + 1, n - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                result.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1

    return result


if __name__ == "__main__":
    def normalize(triplets):
        return sorted(sorted(t) for t in triplets)

    assert normalize(three_sum([-1, 0, 1, 2, -1, -4])) == normalize([[-1, -1, 2], [-1, 0, 1]])
    assert three_sum([0, 1, 1]) == []
    assert three_sum([0, 0, 0]) == [[0, 0, 0]]
    print("All tests passed.")
