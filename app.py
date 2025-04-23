import os
import logging
from flask import Flask, request, jsonify
import requests
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Configuration for third-party APIs
THIRD_PARTY_APIS = {
    'temperature': {
        'url': 'https://api.weatherapi.com/v1/current.json',
        'default_unit': 'celsius',
        'param_name': 'temp',
        'api_key': os.getenv('API_KEY')  # Load API key from .env
    },
    'pressure': {
        'url': 'https://api.weatherapi.com/v1/current.json',
        'default_unit': 'hpa',
        'param_name': 'pressure',
        'api_key': os.getenv('API_KEY')  # Load API key from .env
    },
    'pollutant': {
        'url': 'https://api.weatherapi.com/v1/current.json',
        'default_unit': 'ppm',
        'param_name': 'aqi',
        'api_key': os.getenv('API_KEY')  # Load API key from .env
    }
}

class ValidUnits(Enum):
    TEMPERATURE = ['celsius', 'fahrenheit']
    PRESSURE = ['hpa', 'atm', 'mmhg']
    POLLUTANT = ['ppm', 'ppb', 'µg/m³']

def convert_units(value, from_unit, to_unit, parameter):
    if parameter == 'temperature':
        if from_unit == 'celsius' and to_unit == 'fahrenheit':
            return round((value * 9/5) + 32, 2)
        elif from_unit == 'fahrenheit' and to_unit == 'celsius':
            return round((value - 32) * 5/9, 2)
        return value
    
    elif parameter == 'pressure':
        if from_unit == 'hpa' and to_unit == 'atm':
            return round(value / 1013.25, 4)
        elif from_unit == 'hpa' and to_unit == 'mmhg':
            return round(value * 0.750062, 2)
        return value
    
    elif parameter == 'pollutant':
        if from_unit == 'µg/m³' and to_unit == 'ppm':
            return round(value / 1000, 4) 
        return value

def validate_units(parameter, units):
    valid_units = ValidUnits.__dict__[parameter.upper()].value
    if units.lower() not in valid_units:
        raise ValueError(f"Invalid units for {parameter}. Must be one of: {valid_units}")

@app.route('/temperature', methods=['POST'])
def get_temperature():
    try:
        data = request.get_json()
        if not data or 'units' not in data or 'parameter' not in data:
            return jsonify({'error': 'Missing required parameter: units or parameter'}), 400
        
        parameter = data['parameter'].lower()
        units = data['units'].lower()
        validate_units(parameter, units)
        
        config = THIRD_PARTY_APIS['temperature']
        city_name = data.get('city', 'Hyderabad')
        response = requests.get(
            config['url'],
            params={'key': config['api_key'], 'q': city_name}
        )
        response.raise_for_status()
        
        original_value = response.json()['current']['temp_c']
        converted_value = convert_units(original_value, config['default_unit'], units, 'temperature')
        
        return jsonify({
            'parameter': 'temperature',
            'measured_value': converted_value,
            'units': units,
            'original_value': original_value,
            'original_units': config['default_unit']
        })
        
    except ValueError as e:
        logging.error(f"ValueError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except requests.RequestException as e:
        logging.error(f"RequestException: {str(e)}")
        return jsonify({'error': 'Temperature service error'}), 502  # Return 502 for service errors
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/pressure', methods=['POST'])
def get_pressure():
    try:
        data = request.get_json()
        if not data or 'units' not in data or 'parameter' not in data:
            return jsonify({'error': 'Missing required parameter: units or parameter'}), 400
        
        parameter = data['parameter'].lower()
        units = data['units'].lower()
        validate_units(parameter, units)
        
        config = THIRD_PARTY_APIS['pressure']
        city_name = data.get('city', 'Hyderabad')
        response = requests.get(
            config['url'],
            params={'key': config['api_key'], 'q': city_name}
        )
        response.raise_for_status()
        
        original_value = response.json()['current']['pressure_mb']
        converted_value = convert_units(original_value, config['default_unit'], units, 'pressure')
        
        return jsonify({
            'parameter': 'pressure',
            'measured_value': converted_value,
            'units': units,
            'original_value': original_value,
            'original_units': config['default_unit']
        })
        
    except ValueError as e:
        logging.error(f"ValueError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except requests.RequestException as e:
        logging.error(f"RequestException: {str(e)}")
        return jsonify({'error': 'Pressure service error'}), 502  # Return 502 for service errors
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/pollutant', methods=['POST'])
def get_pollutant():
    try:
        data = request.get_json()
        if not data or 'units' not in data:
            return jsonify({'error': 'Missing required parameter: units'}), 400
            
        units = data['units'].lower()
        
        try:
            validate_units('pollutant', units)
        except ValueError as e:
            logging.error(f"ValueError: {str(e)}")
            return jsonify({'error': str(e)}), 400  # Explicitly return 400 for invalid units
            
        config = THIRD_PARTY_APIS['pollutant']
        city_name = data.get('city', 'Hyderabad')
        
        try:
            response = requests.get(
                config['url'],
                params={
                    'key': config['api_key'],
                    'q': city_name,
                    'aqi': 'yes'
                }
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"RequestException: {str(e)}")
            return jsonify({'error': 'Pollutant service error'}), 502  # Explicitly return 502 for service errors
            
        api_data = response.json()
        
        if 'air_quality' not in api_data['current'] or 'pm2_5' not in api_data['current']['air_quality']:
            return jsonify({'error': 'Air quality data not available'}), 404
            
        original_value = api_data['current']['air_quality']['pm2_5']
        converted_value = convert_units(original_value, 'µg/m³', units, 'pollutant')
        
        return jsonify({
            'parameter': 'pollutant',
            'measured_value': converted_value,
            'units': units,
            'original_value': original_value,
            'original_units': 'µg/m³',
            'city': city_name
        })
        
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
