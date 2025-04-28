# Weather API Project

A Flask-based REST API that fetches weather data from WeatherAPI.com with unit conversion capabilities.

## Features

- Real-time temperature, pressure, and air quality data
- Unit conversion for all measurements
- Error handling with appropriate HTTP status codes
- Comprehensive test suite
How to setup:
WEATHER API PROJECT SETUP

1. Clone the project:
   git clone https://github.com/NareshKalluri-9550/weatherproject.git
   cd weatherproject

2. Create and activate virtual environment:
   - Windows:
     python -m venv venv
     venv\Scripts\activate
   - Mac/Linux:
     python3 -m venv venv
     source venv/bin/activate

3. Install requirements:
   pip install -r requirements.txt
   
4. Run the API:
   python app.py

5. Run tests:
   pytest test_weather_api.py

## API Endpoints
# Celsius with city
curl -X POST http://localhost:5000/temperature -H "Content-Type: application/json" -d "{\"city\": \"London\", \"units\": \"celsius\"}"

# Fahrenheit without city
curl -X POST http://localhost:5000/temperature -H "Content-Type: application/json" -d "{\"units\": \"fahrenheit\"}"

# Invalid units
curl -X POST http://localhost:5000/temperature -H "Content-Type: application/json" -d "{\"units\": \"kelvin\"}"

# hPa with city
curl -X POST http://localhost:5000/pressure -H "Content-Type: application/json" -d "{\"city\": \"Tokyo\", \"units\": \"hpa\"}"

# atm without city
curl -X POST http://localhost:5000/pressure -H "Content-Type: application/json" -d "{\"units\": \"atm\"}"

# mmHg with city
curl -X POST http://localhost:5000/pressure -H "Content-Type: application/json" -d "{\"city\": \"Paris\", \"units\": \"mmhg\"}"

# µg/m³ with city
curl -X POST http://localhost:5000/pollutant -H "Content-Type: application/json" -d "{\"city\": \"Delhi\", \"units\": \"µg/m³\"}"

# ppm without city
curl -X POST http://localhost:5000/pollutant -H "Content-Type: application/json" -d "{\"units\": \"ppm\"}"

# ppb with city
curl -X POST http://localhost:5000/pollutant -H "Content-Type: application/json" -d "{\"city\": \"Beijing\", \"units\": \"ppb\"}"

