#!/bin/bash
cd /Users/leeroy/Documents/Development/edison-ui/.worktrees/happy-pid-9221/backend
export PYTHONPATH=/Users/leeroy/Documents/Development/edison-ui/.worktrees/happy-pid-9221/backend
/Users/leeroy/Documents/Development/edison-ui/backend/.venv/bin/python -m pytest tests/test_agents_tracking.py -v
