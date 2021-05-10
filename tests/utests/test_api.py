from itertools import permutations
import pytest
import psycopg2

from event_provider.interface import PayloadConversionException, HealthException
from nacl.exceptions import CryptoError
from cryptography.exceptions import UnsupportedAlgorithm, AlreadyFinalized

def test_no_body(client):
    response = client.post('/v1/check-bsn')
    assert response.status_code == 400
    response = client.post('/v1/vaccinaties')
    assert response.status_code == 400

@pytest.mark.filterwarnings("ignore::pytest.PytestDeprecationWarning::")
def test_lacking_body(client, subtests):
    response = client.post('/v1/check-bsn', json={'test':'test'})
    assert response.status_code == 400
    required = ["encryptedBsn", "nonce", "hashedBsn"]
    for perm in list(permutations(required)):
        with subtests.test(perm=perm):
            if len(perm) == len(required):
                continue
            data = {}
            for key in perm:
                data[key] = "test"
            response = client.post('/v1/vaccinaties', json=data)
            assert response.status_code == 400

def raise_error(err):
    raise err

@pytest.fixture
def test_data():
    return {
        'encryptedBsn': 'test',
        'nonce': 'test',
        'hashedBsn': 'test'
    }

def test_db_error(client, mocker, test_data):
    mocker.patch('event_provider.api_router.check_information', lambda: raise_error(psycopg2.Error()))
    response = client.post('/v1/check-bsn', json=test_data)
    assert response.status_code == 500
    mocker.patch('event_provider.api_router.get_events', lambda: raise_error(psycopg2.Error()))
    response = client.post('/v1/vaccinaties', json=test_data)
    assert response.status_code == 500

@pytest.mark.filterwarnings("ignore::pytest.PytestDeprecationWarning::")
def test_decrypt_error(client, mocker, subtests, test_data):
    exceptions = [CryptoError(), UnsupportedAlgorithm("test"), AlreadyFinalized()]
    for err in exceptions:
        with subtests.test(err=err):
            mocker.patch('event_provider.api_router.get_events', lambda: raise_error(err))
            response = client.post('/v1/vaccinaties', json=test_data)
            assert response.status_code == 500

def test_conversion_error(client, mocker, test_data):
    mocker.patch('event_provider.api_router.get_events', lambda: raise_error(PayloadConversionException(["test"])))
    response = client.post('/v1/vaccinaties', json=test_data)
    assert response.status_code == 500

def test_health(client, mocker):
    mocker.patch('event_provider.api_router.check_health', return_value=True)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['code'] == 200
    mocker.patch('event_provider.api_router.check_health', lambda: raise_error(HealthException(["test"])))
    response = client.get('/health')
    assert response.status_code == 500
    assert response.json['code'] == 500

def test_check_bsn(client, mocker):
    mocker.patch('event_provider.api_router.check_information', return_value=False)
    response = client.get('/v1/check-bsn', json=test_data)
    assert response.status_code == 200
    assert response.json['exists'] is False
    mocker.patch('event_provider.api_router.check_information', return_value=True)
    response = client.get('/v1/check-bsn', json=test_data)
    assert response.status_code == 200
    assert response.json['exists'] is True
