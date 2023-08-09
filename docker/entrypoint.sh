#!/bin/bash
echo "Activating python .venv"
source /home/app/.venv/bin/activate
exec "$@"