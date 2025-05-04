# alarm_clock.py

import threading
import time
import datetime
import json
import os
from assistant.text_to_speech import speak
from assistant.weather_service import WeatherService

class AlarmClock:
    def __init__(self):
        self.alarms = {}
        self.alarm_threads = {}
        self.alarm_file = "alarms.json"
        self.weather_service = WeatherService()
        self.load_alarms()
        self.start_alarm_threads()

    def load_alarms(self):
        """Load saved alarms from file"""
        if os.path.exists(self.alarm_file):
            try:
                with open(self.alarm_file, 'r') as f:
                    self.alarms = json.load(f)
                print(f"Loaded {len(self.alarms)} alarms from file")
            except Exception as e:
                print(f"Error loading alarms: {e}")
                self.alarms = {}
        else:
            print("No alarm file found. Starting with empty alarms.")
            self.alarms = {}

    def save_alarms(self):
        """Save alarms to file"""
        try:
            with open(self.alarm_file, 'w') as f:
                json.dump(self.alarms, f)
            print(f"Saved {len(self.alarms)} alarms to file")
        except Exception as e:
            print(f"Error saving alarms: {e}")

    def set_alarm(self, hour, minute, days="everyday"):
        """
        Set an alarm for specified time and days
        days can be: "everyday", "weekdays", "weekends", or a comma-separated list of days
        like "monday,wednesday,friday"
        """
        # Validate input
        try:
            hour = int(hour)
            minute = int(minute)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time values")
        except ValueError:
            speak("Invalid time format. Please provide a valid hour (0-23) and minute (0-59).")
            return False

        # Format time for display and as key
        time_key = f"{hour:02d}:{minute:02d}"
        
        # Handle days parameter
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        if days == "everyday":
            alarm_days = valid_days
        elif days == "weekdays":
            alarm_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        elif days == "weekends":
            alarm_days = ["saturday", "sunday"]
        else:
            # Parse custom days
            alarm_days = []
            for day in days.lower().split(","):
                day = day.strip()
                if day in valid_days:
                    alarm_days.append(day)
            
            if not alarm_days:
                speak("No valid days specified. Alarm not set.")
                return False
        
        # Save the alarm
        self.alarms[time_key] = {
            "hour": hour,
            "minute": minute,
            "days": alarm_days,
            "active": True
        }
        
        # Create a thread for this alarm
        self.start_alarm_thread(time_key)
        
        # Save to file
        self.save_alarms()
        
        # Provide feedback
        days_str = ", ".join(alarm_days) if len(alarm_days) <= 3 else f"{len(alarm_days)} days"
        speak(f"Alarm set for {time_key} on {days_str}")
        return True

    def remove_alarm(self, hour, minute):
        """Remove an alarm by hour and minute"""
        time_key = f"{int(hour):02d}:{int(minute):02d}"
        
        if time_key in self.alarms:
            # Stop the thread if it's running
            if time_key in self.alarm_threads:
                self.alarm_threads[time_key]["stop"] = True
                del self.alarm_threads[time_key]
            
            # Remove the alarm
            del self.alarms[time_key]
            self.save_alarms()
            speak(f"Alarm for {time_key} has been removed")
            return True
        else:
            speak(f"No alarm found for {time_key}")
            return False

    def list_alarms(self):
        """List all active alarms"""
        if not self.alarms:
            speak("You have no alarms set")
            return []
        
        alarm_list = []
        for time_key, alarm in self.alarms.items():
            days_str = ", ".join(alarm["days"]) if len(alarm["days"]) <= 3 else f"{len(alarm['days'])} days"
            status = "active" if alarm["active"] else "inactive"
            alarm_info = f"Alarm at {time_key} on {days_str}, {status}"
            alarm_list.append(alarm_info)
            
        # Speak the alarms
        speak(f"You have {len(alarm_list)} alarms set.")
        for alarm in alarm_list:
            speak(alarm)
            
        return alarm_list

    def start_alarm_threads(self):
        """Start threads for all alarms"""
        for time_key in self.alarms:
            self.start_alarm_thread(time_key)

    def start_alarm_thread(self, time_key):
        """Start a thread for a specific alarm"""
        # Stop existing thread if it exists
        if time_key in self.alarm_threads:
            self.alarm_threads[time_key]["stop"] = True
        
        # Create thread data structure
        thread_data = {"stop": False}
        self.alarm_threads[time_key] = thread_data
        
        # Create and start the thread
        thread = threading.Thread(
            target=self._alarm_monitor,
            args=(time_key, thread_data),
            daemon=True
        )
        thread.start()

    def _alarm_monitor(self, time_key, thread_data):
        """Monitor function that runs in its own thread for each alarm"""
        alarm = self.alarms[time_key]
        
        while not thread_data["stop"]:
            # Check if alarm should trigger
            now = datetime.datetime.now()
            current_day = now.strftime("%A").lower()
            
            if (alarm["active"] and 
                now.hour == alarm["hour"] and 
                now.minute == alarm["minute"] and
                current_day in alarm["days"]):
                
                # Trigger the alarm
                self._trigger_alarm(time_key)
                
                # Sleep for 60 seconds to avoid multiple triggers
                time.sleep(60)
            
            # Check every 15 seconds
            time.sleep(15)

    def _trigger_alarm(self, time_key):
        """Trigger the alarm sound and notification with weather information"""
        alarm = self.alarms[time_key]
        now = datetime.datetime.now()
        
        # Determine greeting based on time of day
        hour = now.hour
        if 5 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
            
        # Format time in 12-hour format with AM/PM
        formatted_time = now.strftime("%I:%M %p")
        
        # Get weather information
        weather_data = self.weather_service.get_weather()
        forecast_data = self.weather_service.get_forecast()
        
        # Create the weather part of the message
        if weather_data["success"]:
            location = weather_data["location"]
            temperature = weather_data["temperature"]
            condition = weather_data["description"]
            
            weather_message = f"The weather in {location} is {temperature} degrees Celsius with {condition}."
            
            # Add forecast information if available
            if forecast_data["success"]:
                if forecast_data["rain_expected"]:
                    weather_message += " There is a chance of rain today."
                    
                weather_message += f" Today's temperatures will range from {forecast_data['min_temp']} to {forecast_data['max_temp']} degrees Celsius."
        else:
            # Fallback if weather service is not available
            weather_message = "Weather information is currently unavailable."
        
        # Construct the full alarm message
        message = f"{greeting}! It's {formatted_time}. {weather_message}"
        print(f"\n{message}")
        
        # Speak the alarm message
        speak(message)