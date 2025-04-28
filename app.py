import os
import logging
from flask import Flask, request, jsonify
import requests
from enum import Enum
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

API_KEY = os.getenv('API_KEY')
API_URL = 'https://api.weatherapi.com/v1/current.json'

class ValidUnits(Enum):
    TEMPERATURE = ['celsius', 'fahrenheit']
    PRESSURE = ['hpa', 'atm', 'mmhg']
    POLLUTANT = ['ppm', 'ppb', 'µg/m³']

PARAMS_CONFIG = {
    'temperature': {
        'default_unit': 'celsius',
        'extract': lambda d: d['current']['temp_c']
    },
    'pressure': {
        'default_unit': 'hpa',
        'extract': lambda d: d['current']['pressure_mb']
    },
    'pollutant': {
        'default_unit': 'µg/m³',
        'extract': lambda d: d['current']['air_quality']['pm2_5'],
        'extra': {'aqi': 'yes'}
    }
}

def convert_units(value, from_unit, to_unit, parameter):
    # Ensure that the value is numeric (either int or float)
    if not isinstance(value, (int, float)):
        raise TypeError(f"Invalid value type for {parameter}. Expected a number, got {type(value)}.")
    
    conversions = {
        'temperature': {
            ('celsius', 'fahrenheit'): lambda v: round((v * 9/5) + 32, 2),
            ('fahrenheit', 'celsius'): lambda v: round((v - 32) * 5/9, 2)
        },
        'pressure': {
            ('hpa', 'atm'): lambda v: round(v / 1013.25, 4),
            ('hpa', 'mmhg'): lambda v: round(v * 0.750062, 2)
        },
        'pollutant': {
            ('µg/m³', 'ppm'): lambda v: round(v / 1000, 4)
        }
    }
    
    try:
        return conversions.get(parameter, {}).get((from_unit, to_unit), lambda v: v)(value)
    except Exception as e:
        raise ValueError(f"Conversion failed for {parameter}: {str(e)}")

def validate_units(parameter, units):
    # Ensure the parameter is a string and units is a valid unit
    if not isinstance(parameter, str):
        raise ValueError(f"Invalid parameter type. Expected a string, got {type(parameter)}.")
    if not isinstance(units, str):
        raise ValueError(f"Invalid units type. Expected a string, got {type(units)}.")
    if units.lower() not in ValidUnits[parameter.upper()].value:
        raise ValueError(f"Invalid units for {parameter}. Must be one of: {ValidUnits[parameter.upper()].value}")

def fetch_weather_data(city, extra=None):
    params = {'key': API_KEY, 'q': city}
    if extra:
        params.update(extra)
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def handle_request(parameter):
    try:
        # Check if request is JSON
        if not request.is_json:
            return jsonify({'error': 'Content-type must be application/json'}), 415

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Malformed JSON'}), 400

        # Ensure units is a valid string
        units = str(data.get('units', '')).lower()
        if not units:
            return jsonify({'error': 'Invalid units'}), 400
        
        logging.debug(f"Received request for {parameter} with city: {data.get('city', 'Hyderabad')} and units: {units}")
        
        validate_units(parameter, units)
        config = PARAMS_CONFIG[parameter]
        json_data = fetch_weather_data(data.get('city', 'Hyderabad'), config.get('extra'))

        original_value = config['extract'](json_data)
        converted_value = convert_units(original_value, config['default_unit'], units, parameter)

        return jsonify({
            'parameter': parameter,
            'measured_value': converted_value,
            'units': units,
            'original_value': original_value,
            'original_units': config['default_unit'],
            'city': data.get('city', 'Hyderabad')
        })
    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        return jsonify({'error': str(ve)}), 400
    except requests.RequestException as re:
        logging.error(f"Request error: {re}")
        return jsonify({'error': f'{parameter.capitalize()} service error'}), 502
    except TypeError as te:
        logging.error(f"Type error: {te}")
        return jsonify({'error': str(te)}), 400
    except Exception as e:
        logging.error(f"Unhandled error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/<parameter>', methods=['POST'])
def get_data(parameter):
    if parameter not in PARAMS_CONFIG:
        return jsonify({'error': 'Invalid parameter'}), 400
    return handle_request(parameter)

if __name__ == '__main__':
    app.run(debug=True)
