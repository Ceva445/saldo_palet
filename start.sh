#!/bin/bash
# Local dev start: migrate, seed, run.
set -e

alembic upgrade head
python -m scripts.seed_data
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
