ifeq ($(shell uname -m),arm64)
env = env PATH=${bin}:$$PATH /usr/bin/arch -x86_64
else
env = env PATH=${bin}:$$PATH
endif

venv: .venv/.make_venv_complete
.venv/.make_venv_complete:
	${MAKE} clean
	python3 -m venv .venv
	. .venv/bin/activate; pip install -U pip
	. .venv/bin/activate; pip install -Ur requirements.txt
	. .venv/bin/activate; pip install -Ur requirements-dev.txt
	@touch $@

clean:  ## Remove the virtual environment
	@rm -rf .venv

run: venv
	. .venv/bin/activate; FLASK_APP=event_provider FLASK_ENV=development python -m event_provider

run-prod: venv
	. .venv/bin/activate; FLASK_APP=event_provider FLASK_ENV=production python -m event_provider

wsgi: venv
	# Test if the wsgi file starts an app. The app.run should not be called.
	# See: https://flask.palletsprojects.com/en/1.1.x/deploying/mod_wsgi/#creating-a-wsgi-file
	. .venv/bin/activate; python wsgi.py

audit: venv
    # Checking for trivial security issues
	. .venv/bin/activate; python3 -m bandit -c bandit.yaml -r .

check: venv
	# verify that all pedantic ${shell} issues are resolved.
	. .venv/bin/activate; python3 -m black --check event_provider/

lint: venv
	# Do basic linting
	. .venv/bin/activate; pylint event_provider

fix: venv ## Automatically fix style issues
	# Performing linting
	. .venv/bin/activate; python3 -m black event_provider/

	# Removes unused imports. It makes use of pyflakes to do this.
	. .venv/bin/activate; python3 -m autoflake -ri --remove-all-unused-imports ./
	${MAKE} check

pip-compile:
	# synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate; python3 -m piptools compile requirements.in
	. .venv/bin/activate; python3 -m piptools compile requirements-dev.in

pip-sync-dev:
	# synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate; python3 -m piptools sync requirements.txt requirements-dev.txt

pip-compile-upgrade:
	. .venv/bin/activate; python3 -m piptools compile requirements.in --upgrade
	. .venv/bin/activate; python3 -m piptools compile requirements-dev.in --upgrade

test: venv ## Run all tests
	. .venv/bin/activate; FLASK_APP=event_provider pytest -vv --cov=event_provider --no-cov-on-fail tests/
