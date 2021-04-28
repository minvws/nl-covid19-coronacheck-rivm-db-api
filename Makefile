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
	. .venv/bin/activate; FLASK_APP=event_provider FLASK_ENV=development python -m flask run

run-prod: venv
	. .venv/bin/activate; FLASK_APP=event_provider FLASK_ENV=production python -m flask run

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
	. .venv/bin/activate; FLASK_APP=event_provider pytest -vv --cov=geoproxy --no-cov-on-fail tests/

test-report: venv
	. .venv/bin/activate; coverage report

testcase: venv ## Perform a single testcase, for example make testcase case=my_test
	# add -s to pytest to see live debugging output, add --full-trace  for full tracing of errors.
	@. .venv/bin/activate; python -m pytest -s -vvv -k ${case}