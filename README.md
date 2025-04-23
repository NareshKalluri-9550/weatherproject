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
curl -X POST http://localhost:5000/temperature -H "Content-Type: application/json" -d "{\"parameter\":\"temperature\",\"units\":\"fahrenheit\"}"
{
  "measured_value": 93.92,
  "original_units": "celsius",
  "original_value": 34.4,
  "parameter": "temperature",
  "units": "fahrenheit"
}

curl -X POST http://localhost:5000/pressure -H "Content-Type: application/json" -d "{\"parameter\":\"pressure\",\"units\":\"hpa\"}"
{
  "measured_value": 1014.0,
  "original_units": "hpa",
  "original_value": 1014.0,
  "parameter": "pressure",
  "units": "hpa"
}

curl -X POST http://localhost:5000/pollutant -H "Content-Type: application/json" -d "{\"parameter\":\"pollutant\",\"units\":\"ppm\"}"
{
  "city": "Hyderabad",
  "measured_value": 0.0561,
  "original_units": "\u00b5g/m\u00b3",
  "original_value": 56.055,
  "parameter": "pollutant",
  "units": "ppm"
}
