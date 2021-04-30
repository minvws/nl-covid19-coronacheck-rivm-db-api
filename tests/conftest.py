import pytest

from event_provider import create_app

@pytest.fixture(scope="session")
def app():
    app = create_app()
    yield app


@pytest.fixture(scope="session")
def context(app):
    context = app.app_context()
    context.push()
    yield context


@pytest.fixture(scope="session")
def client(app):
    yield app.test_client()
