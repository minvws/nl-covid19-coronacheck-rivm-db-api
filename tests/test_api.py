from itertools import permutations
import pytest
import psycopg2

def test_no_body(client):
    response = client.post('/v1/check-bsn')
    assert response.status_code == 400
    response = client.post('/v1/vaccinaties')
    assert response.status_code == 400

def test_lacking_body(client):
    response = client.post('/v1/check-bsn', json={'test':'test'})
    assert response.status_code == 400
    required = ["encryptedBsn", "nonce", "hashedBsn"]
    for perm in list(permutations(required)):
        if len(perm) == len(required):
            continue
        data = {}
        for key in perm:
            data[key] = "test"
        response = client.post('/v1/vaccinaties', json=data)
        assert response.status_code == 400

def test_db_error(client, mocker):
    def raise_error():
        raise psycopg2.Error()
    # Weird mock because mocking api confuses Flask
    mocker.patch('event_provider.interface.check_info_db', raise_error)
    response = client.post('/v1/check-bsn', json={'hashedBsn': 'test'})
    assert response.status_code == 500
