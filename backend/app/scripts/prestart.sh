#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python qiushuiai/backend_pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python qiushuiai/initial_data.py
