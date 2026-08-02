// Print "Hello, world!" x times using recursion instead of a loop.
fn recurse(x: i32) {
    if x <= 0 {
        return;
    }
    println!("Hello, world!");
    recurse(x - 1);
}

fn main() {
    recurse(5);
}
