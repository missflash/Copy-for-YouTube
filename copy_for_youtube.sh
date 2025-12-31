#!/bin/bash


# Updated: Use relative path to find the python script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/copy_for_youtube.py"
PYTHON_BIN="/bin/python3"

# 인자값이 있으면 파이썬으로 전달 (예: notify)
$PYTHON_BIN "$SCRIPT_PATH" "$1"