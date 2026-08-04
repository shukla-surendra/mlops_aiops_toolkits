"""3. Evaluate Reverse Polish Notation — Medium
Stack-based postfix evaluation; division truncates toward zero.
"""
from typing import List


def eval_rpn(tokens: List[str]) -> int:
    stack = []
    operators = {"+", "-", "*", "/"}

    for token in tokens:
        if token in operators:
            b = stack.pop()
            a = stack.pop()
            if token == "+":
                stack.append(a + b)
            elif token == "-":
                stack.append(a - b)
            elif token == "*":
                stack.append(a * b)
            else:
                stack.append(int(a / b))
        else:
            stack.append(int(token))

    return stack[-1]


if __name__ == "__main__":
    assert eval_rpn(["2", "1", "+", "3", "*"]) == 9
    assert eval_rpn(["4", "13", "5", "/", "+"]) == 6
    assert eval_rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22
    print("All tests passed.")
