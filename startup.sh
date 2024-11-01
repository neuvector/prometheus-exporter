#!/bin/sh
if [ -f /.venv/bin/activate ]; then
    source /.venv/bin/activate
fi
python3 -u /usr/local/bin/nv_exporter.py "$@"
