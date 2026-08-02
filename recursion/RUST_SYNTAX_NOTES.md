# Rust syntax notes

Running notes on Rust language features encountered while solving problems
in this crate, for reference.

## `match`

From `008_nth_fibonacci_recursion.rs`:

```rust
fn fib(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fib(n - 1) + fib(n - 2),
    }
}
```

`match` is Rust's pattern-matching control-flow expression - similar in
spirit to a `switch` statement in C/Java/JS, but stricter and more
powerful. It compares `n` against a series of *patterns*, top to bottom,
and runs the code for the first one that matches.

- `0 => 0` - a *pattern*: if `n` equals the literal `0`, the arm evaluates
  to `0`.
- `1 => 1` - same idea: if `n` equals `1`, the arm evaluates to `1`.
- `_ => fib(n - 1) + fib(n - 2)` - `_` is the *wildcard pattern*, matching
  anything not caught by an earlier arm (here, any `n >= 2`, since `u64`
  can't be negative). It plays the role of `default:` in a `switch`.

Key properties that make `match` different from `switch`:

- **Exhaustive**: the compiler requires every possible value of `n` to be
  covered by some arm. This `match` compiles only because `_` catches
  everything else - remove it and the compiler rejects the code with a
  "non-exhaustive patterns" error. This is what prevents the equivalent of
  an accidentally-unhandled `switch` case.
- **No fallthrough**: unlike C's `switch`, execution never "falls through"
  from one arm to the next. Each arm is self-contained; only one arm runs.
- **It's an expression, not a statement**: the whole `match` evaluates to a
  value (whichever arm ran), which is why `match n { ... }` can be the last
  line of `fib` with no `return` or trailing `;` - its value is the
  function's implicit return value, the same convention used for the
  `if`/`else` versions in `003_recursive_factorial.rs` and
  `005_return_recursion_sum.rs`.
- **Patterns can be much richer than literals**: ranges (`2..=10`), multiple
  values per arm (`0 | 1 => ...`), destructuring of tuples/structs/enums,
  and binding with guards (`n if n > 100 => ...`) are all valid - literal
  values and `_` are just the simplest case, shown here because that's all
  `fib` needs.

Compare with the `if`/`else` form used in earlier problems
(`003_recursive_factorial.rs`, `006_reverse_array_recursion.rs`,
`007_palindrome_string_recursion.rs`):

```rust
fn factorial(n: u32) -> u32 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Both compile to equivalent code for a simple two-way branch; `match`
becomes the better fit once there are 3+ distinct cases (like `fib`'s two
base cases plus the recursive case) since it reads as a flat list of
cases instead of a nested `if`/`else if`/`else` chain.
