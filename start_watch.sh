#!/bin/bash
cd fast_typst || return
cargo run --release -- watch ../main.typ
