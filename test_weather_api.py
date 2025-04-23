import pytest
from unittest.mock import patch
import requests
from flask import json
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Positive Test Cases
@patch('app.requests.get')
def test_get_temperature_success(mock_get, client):
    mock_get.return_value.json.return_value = {'current': {'temp_c': 20}}
    mock_get.return_value.status_code = 200

    response = client.post('/temperature', json={"parameter": "temperature", "units": "fahrenheit"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['measured_value'] == 68.0  # 20°C to °F conversion
    assert data['original_units'] == 'celsius'

@patch('app.requests.get')
def test_get_pressure_success(mock_get, client):
    mock_get.return_value.json.return_value = {'current': {'pressure_mb': 1013}}
    mock_get.return_value.status_code = 200

    response = client.post('/pressure', json={"parameter": "pressure", "units": "atm"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['measured_value'] == pytest.approx(0.999, rel=1e-3)  # 1013 hPa to atm conversion
    assert data['original_units'] == 'hpa'

@patch('app.requests.get')
def test_get_pollutant_success(mock_get, client):
    mock_get.return_value.json.return_value = {'current': {'air_quality': {'pm2_5': 12}}}
    mock_get.return_value.status_code = 200

    response = client.post('/pollutant', json={"parameter": "pollutant", "units": "ppm"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['measured_value'] == pytest.approx(0.012, rel=1e-3)  # 12 µg/m³ to ppm conversion
    assert data['original_units'] == 'µg/m³'

# Negative Test Cases
@patch('app.requests.get')
def test_get_temperature_invalid_units(mock_get, client):
    response = client.post('/temperature', json={"parameter": "temperature", "units": "invalid"})
    assert response.status_code == 400
    assert b'Invalid units for temperature.' in response.data

@patch('app.requests.get')
def test_get_pressure_invalid_units(mock_get, client):
    response = client.post('/pressure', json={"parameter": "pressure", "units": "invalid"})
    assert response.status_code == 400
    assert b'Invalid units for pressure.' in response.data

@patch('app.requests.get')
def test_get_pollutant_invalid_units(mock_get, client):
    response = client.post('/pollutant', json={"parameter": "pollutant", "units": "invalid"})
    assert response.status_code == 400
    assert b'Invalid units for pollutant.' in response.data

@patch('app.requests.get')
def test_get_temperature_service_error(mock_get, client):
    mock_get.side_effect = requests.RequestException("Service not available")

    response = client.post('/temperature', json={"parameter": "temperature", "units": "fahrenheit"})
    assert response.status_code == 502
    assert b'Temperature service error' in response.data

@patch('app.requests.get')
def test_get_pressure_service_error(mock_get, client):
    mock_get.side_effect = requests.RequestException("Service not available")

    response = client.post('/pressure', json={"parameter": "pressure", "units": "atm"})
    assert response.status_code == 502
    assert b'Pressure service error' in response.data

@patch('app.requests.get')
def test_get_pollutant_service_error(mock_get, client):
    mock_get.side_effect = requests.RequestException("Service not available")

    response = client.post('/pollutant', json={"parameter": "pollutant", "units": "ppm"})
    assert response.status_code == 502
    assert b'Pollutant service error' in response.data
