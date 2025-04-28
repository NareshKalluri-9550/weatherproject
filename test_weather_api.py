import pytest
from unittest.mock import patch, MagicMock
from app import app, convert_units, validate_units, PARAMS_CONFIG
import json
import requests

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Mock data for API responses
MOCK_RESPONSES = {
    'temperature': {
        'current': {'temp_c': 25.0, 'temp_f': 77.0},
        'location': {'name': 'Hyderabad'}
    },
    'pressure': {
        'current': {'pressure_mb': 1013.0},
        'location': {'name': 'Hyderabad'}
    },
    'pollutant': {
        'current': {'air_quality': {'pm2_5': 12.5}},
        'location': {'name': 'Hyderabad'}
    }
}

# Updated PARAMS_CONFIG with URLs
PARAMS_CONFIG = {
    'temperature': {
        'url': 'https://api.weatherapi.com/v1/current.json',
        'units': 'metric'
    },
    'pressure': {
        'url': 'https://api.weatherapi.com/v1/current.json',
        'units': 'metric'
    },
    'pollutant': {
        'url': 'https://api.weatherapi.com/v1/current.json',
        'aqi': 'yes'
    }
}

# Assumptions about 3rd party API expectations
THIRD_PARTY_API_EXPECTATIONS = {
    'temperature': {
        'params': {
            'q': str,          # City name should be string
            'units': str,      # Should be 'metric' or 'imperial'
            'aqi': str         # Should be 'yes' or 'no'
        },
        'required': ['q']
    },
    'pressure': {
        'params': {
            'q': str,
            'units': str,
            'aqi': str
        },
        'required': ['q']
    },
    'pollutant': {
        'params': {
            'q': str,
            'aqi': str         # Must be 'yes' for pollutant
        },
        'required': ['q', 'aqi']
    }
}

class TestUtilityFunctions:
    """Tests for standalone utility functions"""
    
    # Temperature conversion tests
    @pytest.mark.parametrize("from_u,to_u,in_v,out_v", [
        ('celsius', 'fahrenheit', 0, 32.0),
        ('celsius', 'fahrenheit', 100, 212.0),
        ('fahrenheit', 'celsius', 32, 0.0),
        ('fahrenheit', 'celsius', 212, 100.0),
        ('celsius', 'celsius', 10, 10.0)  # no conversion
    ])
    def test_temp_conversion(self, from_u, to_u, in_v, out_v):
        assert convert_units(in_v, from_u, to_u, 'temperature') == pytest.approx(out_v)

    # Test for invalid conversion input types
    @pytest.mark.parametrize("in_v, from_u, to_u, param", [
        ('not_a_number', 'celsius', 'fahrenheit', 'temperature'),
        (100, 'celsius', 'fahrenheit', 'temperature'),
        ('temperature', 'celsius', 'fahrenheit', 789)  # invalid param type
    ])
    def test_invalid_conversion_input_types(self, in_v, from_u, to_u, param):
        if isinstance(in_v, (int, float)):
            # Handle valid cases for conversion
            result = convert_units(in_v, from_u, to_u, param)
            assert isinstance(result, (int, float))  # Assuming return type is int/float
        else:
            # Handle invalid input and ensure error is raised
            with pytest.raises((TypeError, ValueError)):
                convert_units(in_v, from_u, to_u, param)
    # Test valid conversions
    @pytest.mark.parametrize("value,from_u,to_u,param,expected", [
        (100, 'celsius', 'fahrenheit', 'temperature', 212),
        (32, 'fahrenheit', 'celsius', 'temperature', 0),
        (1013.25, 'hpa', 'atm', 'pressure', 1),
        (1013.25, 'hpa', 'mmhg', 'pressure', 760),
        (1000, 'µg/m³', 'ppm', 'pollutant', 1)
    ])
    def test_valid_conversion(self, value, from_u, to_u, param, expected):
        result = convert_units(value, from_u, to_u, param)
        assert result == expected

    # Pressure conversion tests
    @pytest.mark.parametrize("from_u,to_u,in_v,out_v", [
        ('hpa', 'atm', 1013.25, 1.0),
        ('hpa', 'mmhg', 1013.25, 759.81),
        ('hpa', 'hpa', 1000, 1000.0)  # no conversion
    ])
    def test_pressure_conversion(self, from_u, to_u, in_v, out_v):
        assert convert_units(in_v, from_u, to_u, 'pressure') == pytest.approx(out_v, rel=1e-2)

    # Pollutant conversion tests
    @pytest.mark.parametrize("from_u,to_u,in_v,out_v", [
        ('µg/m³', 'ppm', 1000, 1.0),
        ('µg/m³', 'µg/m³', 500, 500.0)  # no conversion
    ])
    def test_pollutant_conversion(self, from_u, to_u, in_v, out_v):
        assert convert_units(in_v, from_u, to_u, 'pollutant') == pytest.approx(out_v)

    # Unit validation tests
    @pytest.mark.parametrize("param,unit,valid", [
        ('temperature', 'celsius', True),
        ('temperature', 'kelvin', False),
        ('pressure', 'hpa', True),
        ('pressure', 'psi', False),
        ('pollutant', 'ppm', True),
        ('pollutant', 'mg/m³', False)
    ])
    def test_unit_validation(self, param, unit, valid):
        if valid:
            validate_units(param, unit)
        else:
            with pytest.raises(ValueError):
                validate_units(param, unit)

    # Test invalid parameter type for validation
    @pytest.mark.parametrize("param,unit", [
        (123, 'celsius'),     # invalid param type
        ('temperature', 456)  # invalid unit type
    ])
    def test_invalid_validation_input_types(self, param, unit):
        with pytest.raises(ValueError):
            validate_units(param, unit)

class BaseTestClass:
    """Base class with common setup methods"""
    
    def setup_mock(self, param, city="Hyderabad"):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            **MOCK_RESPONSES[param],
            'location': {'name': city}
        }
        mock_resp.raise_for_status.return_value = None
        return mock_resp

class TestAPIEndpoints(BaseTestClass):
    """Tests for API endpoints with mocked external API calls"""
    
    def verify_third_party_api_call(self, mock_get, param, expected_params):
        mock_get.assert_called_once()  # Ensure the API was called once
        args, kwargs = mock_get.call_args  # Get the call arguments
        
        # Verify the correct URL is being used
        assert args[0] == PARAMS_CONFIG[param]['url']
        
        actual_params = kwargs['params']
        
        # Check that all required parameters are present
        for req_param in THIRD_PARTY_API_EXPECTATIONS[param]['required']:
            assert req_param in actual_params, f'Missing required param: {req_param}'
        
        # Check that all expected parameters are of the correct type and format
        for k, v in expected_params.items():
            if k in actual_params:
                # Validate `q` (city name) as a string
                if k == 'q':
                    assert isinstance(actual_params[k], str), f"Expected {k} to be a string, but got {type(actual_params[k])}"
                
                # Validate `aqi` as a string
                if k == 'aqi':
                    assert isinstance(actual_params[k], str), f"Expected {k} to be a string, but got {type(actual_params[k])}"
                
                # Ensure v is a valid type (if v is a type)
                elif isinstance(v, type):  
                    assert isinstance(actual_params[k], v), f'Invalid type for {k}, expected {v} but got {type(actual_params[k])}'
                else:
                    raise TypeError(f"Expected type for {k} is not a valid type: {v}")
                
                assert actual_params[k] == expected_params[k], f'Expected value for {k}: {expected_params[k]}, but got {actual_params[k]}'

    @patch('app.requests.get')
    def test_temperature_api(self, mock_get, client):
        mock_get.return_value = self.setup_mock('temperature')
        
        # Test API call
        response = client.post('/temperature', json={'units': 'fahrenheit', 'city': 'Hyderabad'})
        
        # Assert that the response status is 200 (OK)
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Assert that the temperature values are correct
        # Convert Celsius to Fahrenheit for the assertion (25.0 Celsius = 77.0 Fahrenheit)
        assert data['measured_value'] == 77.0  # Expected temperature in Fahrenheit
        assert data['original_value'] == 25.0  # Expected original value in Celsius
        
        # Verify the API parameters sent to the third-party service
        self.verify_third_party_api_call(
            mock_get,
            'temperature',
            {'city': 'Hyderabad', 'units': 'metric'}  # Ensure 'units' is 'metric' (Celsius)
        )

    @patch('app.requests.get')
    def test_pressure_api(self, mock_get, client):
        mock_get.return_value = self.setup_mock('pressure', 'London')
        
        response = client.post('/pressure', json={
            'units': 'atm',
            'city': 'London'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['measured_value'] == pytest.approx(1.0, rel=1e-3)
        assert data['city'] == 'London'

        # Verify API parameters and types
        self.verify_third_party_api_call(
            mock_get,
            'pressure',
            {'city': 'London', 'units': 'metric'}
        )

    @patch('app.requests.get')
    def test_pollutant_api(self, mock_get, client):
        mock_get.return_value = self.setup_mock('pollutant')
        
        # Test API call with 'aqi' set to 'yes'
        response = client.post('/pollutant', json={'units': 'ppm', 'city': 'Hyderabad'})
        
        # Assert that the response status is 200 (OK)
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Validate the expected pollutant data
        assert data['measured_value'] == pytest.approx(0.0125)
        
        # Verify the API parameters sent to the third-party service
        self.verify_third_party_api_call(
            mock_get,
            'pollutant',
            {'city': 'Hyderabad', 'aqi': 'yes'}  # Ensure 'aqi' is passed as 'yes'
        )

class TestErrorScenarios(BaseTestClass):
    """Tests for error handling and edge cases"""
    
    def test_invalid_endpoint(self, client):
        response = client.post('/invalid', json={'units': 'test'})
        assert response.status_code == 400
        assert 'Invalid parameter' in json.loads(response.data)['error']

    @patch('app.requests.get')
    def test_api_failure(self, mock_get, client):
        mock_get.side_effect = requests.RequestException("API Unavailable")
        
        response = client.post('/temperature', json={'units': 'celsius'})
        assert response.status_code == 502
        assert 'service error' in json.loads(response.data)['error']

    @patch('app.requests.get')
    def test_invalid_api_response(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'invalid': 'response'}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        
        response = client.post('/temperature', json={'units': 'celsius'})
        assert response.status_code == 500
        assert 'Internal server error' in json.loads(response.data)['error']