// Problem: you're climbing a staircase with n steps. Each move you can
// climb either 1 or 2 steps. In how many distinct ways can you reach the
// top (step n)?
//
// e.g. n = 3, the distinct ways are:
//   1+1+1, 1+2, 2+1
// -> 3 ways.
//
// Why this is DP: to reach step n, your LAST move was either a 1-step
// (meaning you were previously at step n-1) or a 2-step (meaning you were
// previously at step n-2) - there's no other way to land exactly on step
// n. So the number of ways to reach step n is the number of ways to reach
// step n-1, plus the number of ways to reach step n-2:
//
//   ways(n) = ways(n - 1) + ways(n - 2)
//
// That's the Fibonacci recurrence, verbatim - this problem IS Fibonacci,
// just arrived at through a different story (counting paths instead of
// "sum of the previous two numbers"). It's a common first "aha" in DP:
// very different-sounding problems can reduce to the exact same
// recurrence once you find the right way to define the subproblem
// (here, "ways to reach step i" as the thing to tabulate).
//
// Base cases:
//   ways(0) = 1   // already at the top with zero steps taken - one way: do nothing
//   ways(1) = 1   // only one path to a single step: a single 1-step move
// (Compare to actual Fibonacci, where fib(0) = 0 - the base cases differ
// even though the recurrence is identical, so double check base cases
// whenever you spot a "this is just Fibonacci" reduction; don't assume
// they carry over.)
//
// e.g. ways(4): table = [1, 1, _, _, _]
//   i=2: table[2] = table[1] + table[0] = 1 + 1 = 2
//   i=3: table[3] = table[2] + table[1] = 2 + 1 = 3
//   i=4: table[4] = table[3] + table[2] = 3 + 2 = 5
//   ways(4) = 5, and indeed: 1+1+1+1, 1+1+2, 1+2+1, 2+1+1, 2+2 -> 5 ways.
//
// Complexity: O(n) time, O(n) space with a full table (as written below) -
// same bottom-up/tabulation approach as
// 002_nth_fibonacci_tabulation.rs. Same O(1)-space rolling-variables
// optimization applies here too (the loop only ever reads the last two
// table entries), left as a follow-up once this version is comfortable.

fn ways(n: u64) -> u64 {
    todo!(
        "handle n == 0 separately (table[1] would be out of bounds for a \
        size-1 table); otherwise build a table (Vec<u64>) of size n + 1, \
        set table[0] = 1 and table[1] = 1 as base cases, then loop i from \
        2 to n filling table[i] = table[i-1] + table[i-2]; return table[n]"
    )
}

fn main() {
    for n in 0..10 {
        println!("ways({}) = {}", n, ways(n));
    }
}
