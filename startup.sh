#!/bin/sh
if [ -f /.venv/bin/activate ]; then
    source /.venv/bin/activate
fi
python -u /usr/local/bin/nv_exporter.py "$@"
