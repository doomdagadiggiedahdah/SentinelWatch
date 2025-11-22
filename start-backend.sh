#!/bin/bash
cd "$(dirname "$0")/backend"
source .venv/bin/activate.fish
uvicorn backend.main:app --reload --port 8000
