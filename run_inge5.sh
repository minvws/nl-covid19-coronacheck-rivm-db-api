#!/bin/bash
[[ -d .venv ]] && source .venv/bin/activate
[[ -f .env ]] && source .env

if [[ "$(command -v uwsgi)" ]]
then
	uwsgi --ini uwsgi.ini
else
	FLASK_APP=event_provider FLASK_ENV=production python -m event_provider
fi
