#!/bin/bash
uv venv -p 3.13 --allow-existing
source .venv/bin/activate
python -m ensurepip --default-pip
python -m pip install -r requirements.txt
