#!/bin/bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload --timeout 300 --worker-class sync --worker-connections 1000 main:app
