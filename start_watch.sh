#!/bin/bash
cd fast_typst || exit
cargo run --release -- watch ../main.typ
