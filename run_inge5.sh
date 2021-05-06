#!/bin/bash
[[ -d .venv ]] && source .venv/bin/activate
[[ -f .env ]] && source .env

FLASK_APP=event_provider FLASK_ENV=production python -m event_provider
