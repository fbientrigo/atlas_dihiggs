#!/usr/bin/env bash
# Compatibility entry point; canonical bootstrap is workspace-wide.
exec python3 -P "$(dirname "$0")/../scripts/bootstrap_workspace.py" "$@"
