import os
import pytest

from event_provider import create_app
from nacl.public import PrivateKey
import nacl.utils

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

@pytest.fixture
def bob_keys():
    privkey = PrivateKey.generate()
    return {
        'privkey': privkey,
        'pubkey': privkey.public_key
    }

@pytest.fixture
def alice_keys():
    privkey = PrivateKey.generate()
    return {
        'privkey': privkey,
        'pubkey': privkey.public_key
    }

@pytest.fixture
def rnonce():
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return nonce

@pytest.fixture
def riv():
    return os.urandom(16)
