# rust_dsa_problems
Rust dsa problems

## Running a problem

Each topic (`recursion`, `binary_search_tree`, ...) is its own Cargo crate.
Every problem file under a crate's `src/bin/` directory is a separate binary,
named after the file (without `.rs`).

Run one from inside the crate directory:

```
cd recursion
cargo run --bin 006_reverse_array_recursion
```

Or from the repo root, using `--manifest-path`:

```
cargo run --manifest-path recursion/Cargo.toml --bin 006_reverse_array_recursion
```

List the available binaries in a crate with:

```
cargo run --bin
```

(passing no name prints the list of valid `--bin` targets and exits)

## Ad-hoc single-file scripts

For standalone `.rs` files that aren't part of a crate:

```
f=dijkstra; rustc $f.rs -o $f.bin && ./$f.bin
```
