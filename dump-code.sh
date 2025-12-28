#!/usr/bin/bash

echo "===== Project structure:"

tree -I __pycache__

find . -name '*.py' | fgrep -v .venv/ | while read FILE; do
    echo "===== Content of ${FILE}:"
    cat "${FILE}"
done
