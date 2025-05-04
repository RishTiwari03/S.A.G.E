# weather_service.py

import requests
import json
import os

class WeatherService:
    def __init__(self):
        # Store API key and location in a config file
        self.config_file = "weather_config.json"
        self.api_key = ""
        self.location = "London"  # Default location
        self.load_config()
        
    def load_config(self):
        """Load API key and location from config file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", "")
                    self.location = config.get("location", "London")
                print(f"Loaded weather config for {self.location}")
            except Exception as e:
                print(f"Error loading weather config: {e}")
        else:
            print("No weather config file found. Using defaults.")
            self.save_config()
            
    def save_config(self):
        """Save API key and location to config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    "api_key": self.api_key,
                    "location": self.location
                }, f)
            print(f"Saved weather config for {self.location}")
        except Exception as e:
            print(f"Error saving weather config: {e}")
            
    def set_location(self, location):
        """Update the location for weather forecasts"""
        self.location = location
        self.save_config()
        return True
        
    def set_api_key(self, api_key):
        """Update the API key for weather service"""
        self.api_key = api_key
        self.save_config()
        return True
        
    def get_weather(self):
        """Get current weather data for the configured location"""
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key configured. Please set up an OpenWeatherMap API key."
            }
            
        try:
            # Using OpenWeatherMap API for weather data
            url = f"http://api.openweathermap.org/data/2.5/weather?q={self.location}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Error fetching weather data: {response.status_code}"
                }
                
            data = response.json()
            
            # Extract relevant weather information
            weather = {
                "success": True,
                "location": self.location,
                "temperature": round(data["main"]["temp"]),
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "icon": data["weather"][0]["icon"]
            }
            
            return weather
            
        except Exception as e:
            print(f"Error getting weather: {e}")
            return {
                "success": False,
                "error": f"Error getting weather: {str(e)}"
            }
    
    def get_forecast(self):
        """Get weather forecast for the day"""
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key configured. Please set up an OpenWeatherMap API key."
            }
            
        try:
            # Using OpenWeatherMap API for forecast data
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={self.location}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Error fetching forecast data: {response.status_code}"
                }
                
            data = response.json()
            
            # Process forecast data (next 24 hours)
            forecasts = []
            for item in data["list"][:8]:  # First 8 entries = 24 hours (3-hour steps)
                forecast = {
                    "time": item["dt_txt"],
                    "temperature": round(item["main"]["temp"]),
                    "condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "rain": item["rain"]["3h"] if "rain" in item else 0
                }
                forecasts.append(forecast)
            
            # Check for rain in the next 24 hours
            rain_forecast = any(f["rain"] > 0 for f in forecasts)
            max_temp = max(f["temperature"] for f in forecasts)
            min_temp = min(f["temperature"] for f in forecasts)
            
            return {
                "success": True,
                "forecasts": forecasts,
                "rain_expected": rain_forecast,
                "max_temp": max_temp,
                "min_temp": min_temp
            }
            
        except Exception as e:
            print(f"Error getting forecast: {e}")
            return {
                "success": False,
                "error": f"Error getting forecast: {str(e)}"
            }