# commands.py 

import webbrowser
import glob
import os
import re
import psutil
import time
import pyautogui
import subprocess
import smtplib
import requests
import datetime
import threading
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import getpass
from pywinauto import Desktop
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from assistant.text_to_speech import speak, speaking, speech_lock
from assistant.voice_recognition import listen
from assistant.weather_service import WeatherService
from assistant.alarm_clock import AlarmClock

# Check if facial recognition is available
facial_recognition_available = False
try:
    from assistant.facial_recognition import FacialRecognizer
    facial_recognition_available = True
    print("Facial recognition imported successfully in commands.py")
except ImportError:
    print("Facial recognition module not available. Face-related commands will be disabled.")
except Exception as e:
    print(f"Error importing facial recognition: {e}")

class Commands:
    def __init__(self):
        # Define commonly used application names for portability
        self.common_applications = {
            "notepad": "notepad",
            "calculator": "calc",
            "google": "chrome",
            "disc": "discord",
            "spotify": "spotify",
            "word": "winword"  # Typically for Microsoft Word
        }

        # Initialize audio interface for system volume control
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume_control = cast(interface, POINTER(IAudioEndpointVolume))

        # SMTP server configurations for common email providers
        self.smtp_configs = {
            "gmail": {"server": "smtp.gmail.com", "port": 587},
            "outlook": {"server": "smtp-mail.outlook.com", "port": 587},
            "yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
        }
        
        # Initialize the weather service and alarm clock
        self.weather_service = WeatherService()
        self.alarm_clock = AlarmClock()
        
        # Initialize facial recognition if available
        self.facial_recognition_available = facial_recognition_available
        self.face_recognizer = None
        if self.facial_recognition_available:
            try:
                self.face_recognizer = FacialRecognizer()
                print("Facial recognition initialized in Commands class")
            except Exception as e:
                print(f"Error initializing facial recognition in Commands: {e}")
                self.facial_recognition_available = False
                
        # Flags for command flow control
        self.in_conversation = False
        self.conversation_command = ""
        self.waiting_for_response = False
        
        # Thread locking to prevent overlapping command processing
        self.command_lock = threading.Lock()

    def process_command(self, command):
        """Directs the command to the appropriate function based on keywords."""
        # Use lock to ensure only one command is processed at a time
        with self.command_lock:
            # Check if we're in the middle of a conversation flow
            if self.in_conversation:
                # Special commands that can interrupt a conversation
                if "mute" in command or "stop" in command or "cancel" in command:
                    self.in_conversation = False
                    speak("Command cancelled.")
                    return
                
                # Handle the current conversation based on its type
                if self.conversation_command == "open_website":
                    self.in_conversation = False
                    self.open_website(command)
                    return
                elif self.conversation_command == "search_google":
                    self.in_conversation = False
                    self.search_google_with_term(command)
                    return
                elif self.conversation_command == "play_youtube":
                    self.in_conversation = False
                    self.play_youtube_with_term(command)
                    return
                # Add more conversation flows as needed
            
            # If not in a conversation, process as a new command
            if "mute" in command:
                speak("Assistant paused.")
                return
                
            if "search" in command:
                if command.replace("search", "").strip():
                    # If the search term is included in the command
                    search_term = command.replace("search", "").strip()
                    self.search_google_with_term(search_term)
                else:
                    # Start a conversation to get the search term
                    self.conversation_command = "search_google"
                    self.in_conversation = True
                    speak("What would you like to search?")
            elif "play video" in command or "play youtube" in command:
                if "for" in command and len(command.split("for", 1)[1].strip()) > 0:
                    # If the video term is included in the command
                    video_term = command.split("for", 1)[1].strip()
                    self.play_youtube_with_term(video_term)
                else:
                    # Start a conversation to get the video term
                    self.conversation_command = "play_youtube"
                    self.in_conversation = True
                    speak("What would you like to watch?")
            elif "open website" in command:
                if "open website" != command.strip():
                    # If website name is included in the command
                    website = command.replace("open website", "").strip()
                    self.open_website(website)
                else:
                    # Start a conversation to get the website name
                    self.conversation_command = "open_website"
                    self.in_conversation = True
                    speak("Please specify the name of the website you want to open.")
            elif "open file" in command:
                self.open_file()
            elif "open" in command:
                self.open_application(command)
            elif "increase volume" in command:
                self.adjust_system_volume("increase")
            elif "decrease volume" in command:
                self.adjust_system_volume("decrease")
            elif "write essay" in command:
                self.write_essay()
            elif "send email" in command or "write email" in command:
                self.send_email()
            elif "change email settings" in command:
                self.change_email_settings()
            # Weather commands
            elif "set location" in command:
                self.set_weather_location()
            elif "set weather api" in command or "set api key" in command:
                self.set_weather_api_key()
            elif "get weather" in command or "weather" in command or "forecast" in command:
                self.get_current_weather()
            # Alarm commands
            elif "set alarm" in command or "wake me up" in command:
                self.set_alarm()
            elif "remove alarm" in command or "delete alarm" in command:
                self.remove_alarm()
            elif "list alarms" in command or "show alarms" in command:
                self.list_alarms()
            # Face recognition commands - check if available first
            elif self.facial_recognition_available and ("add face" in command or "add user" in command or "register face" in command):
                self.add_face_user()
            elif self.facial_recognition_available and ("list users" in command or "list faces" in command):
                self.list_face_users()
            elif self.facial_recognition_available and ("remove user" in command or "delete user" in command):
                self.remove_face_user()
            elif self.facial_recognition_available and ("recognize face" in command or "recognize me" in command or "who am i" in command):
                self.recognize_face()
            elif "add face" in command or "add user" in command or "register face" in command or "list users" in command or "list faces" in command or "remove user" in command or "delete user" in command or "recognize face" in command or "recognize me" in command or "who am i" in command:
                # Handle facial recognition commands when facial recognition is not available
                speak("I'm sorry, facial recognition is not available. Please check if OpenCV is installed correctly.")
            else:
                # If in GUI mode, don't say "I didn't understand" for basic commands
                # This prevents confusion with the continuous listener thread
                # Uncomment the following line for CLI mode:
                # speak("I'm sorry, I didn't understand that command.")
                pass

    def adjust_system_volume(self, action):
        """Increases or decreases the system volume."""
        current_volume = self.volume_control.GetMasterVolumeLevelScalar()  # Get volume as scalar (0.0 to 1.0)
        
        if action == "increase" and current_volume < 1.0:
            new_volume = min(1.0, current_volume + 0.1)
        elif action == "decrease" and current_volume > 0.0:
            new_volume = max(0.0, current_volume - 0.1)
        else:
            new_volume = current_volume  # No change if at max or min

        self.volume_control.SetMasterVolumeLevelScalar(new_volume, None)  # Set volume
        speak(f"Volume {'increased' if action == 'increase' else 'decreased'} to {int(new_volume * 100)} percent.")

    def open_file(self):
        """Prompts the user for a file name and attempts to open it without needing the extension."""
        speak("Please tell me the name of the file you want to open.")
        response = self.get_response()

        if response:
            # Define the search directory
            search_path = "C:/Users"  # Starting directory to search (customize as needed)
            speak(f"Searching for files named {response} on your computer.")
            
            # Search for files matching the name without extension
            file_paths = glob.glob(f"{search_path}/**/{response}.*", recursive=True)

            if file_paths:
                try:
                    os.startfile(file_paths[0])  # Open the first file found
                    speak(f"Opening the file {response}")
                except Exception as e:
                    speak("Sorry, I couldn't open the file.")
                    print(f"Error: {e}")
            else:
                speak("I couldn't find a file with that name. Please make sure the name is correct.")

    def search_google_with_term(self, search_term):
        """Directly search Google with the provided term."""
        if search_term:
            url = f"https://www.google.com/search?q={search_term}"
            speak(f"Searching Google for {search_term}")
            webbrowser.open(url)
            
    def play_youtube_with_term(self, video_term):
        """Directly search YouTube with the provided term."""
        if video_term:
            url = f"https://www.youtube.com/results?search_query={video_term}"
            speak(f"Playing YouTube video for {video_term}")
            webbrowser.open(url)
                
    def open_website(self, website_name):
        """Opens a website, assuming '.com' if not specified."""
        if website_name:
            # Check if it's one of the common websites
            if website_name.lower() in ["google", "google.com"]:
                webbrowser.open("https://www.google.com")
                speak(f"Opening Google")
                return
            elif website_name.lower() in ["youtube", "youtube.com"]:
                webbrowser.open("https://www.youtube.com")
                speak(f"Opening YouTube")
                return
            elif website_name.lower() in ["facebook", "facebook.com"]:
                webbrowser.open("https://www.facebook.com")
                speak(f"Opening Facebook")
                return
            
            # Clean and process the input
            website_name = website_name.strip().lower()

            # Add '.com' if the user does not specify a domain or extension
            if "." not in website_name:
                website_name = f"{website_name}.com"

            # Add 'http://' if no protocol is specified
            if not website_name.startswith(("http://", "https://")):
                website_name = f"http://{website_name}"

            # Validate the URL structure with a regex
            url_pattern = re.compile(
                r'^(http://|https://)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/.*)?$'
            )
            if url_pattern.match(website_name):
                try:
                    webbrowser.open(website_name)
                    speak(f"Opening {website_name}")
                except Exception as e:
                    speak("Sorry, I encountered an error while opening the website.")
                    print(f"Error: {e}")
            else:
                speak("The website address seems invalid. Please try again.")

    def write_essay(self):
        """Prompts the user to dictate content for an essay."""
        speak("What is the topic of your essay?")
        topic = self.get_response()
        if topic:
            speak(f"Starting an essay on {topic}. Please dictate your sentences, say 'stop' when done.")
            essay_content = []
            while True:
                sentence = self.get_response()
                if sentence and "stop" in sentence.lower():
                    break
                elif sentence:
                    essay_content.append(sentence)
            if essay_content:
                essay_text = " ".join(essay_content)
                with open("Essay_on_" + topic.replace(" ", "_") + ".txt", "w") as f:
                    f.write(essay_text)
                speak("Essay has been written and saved.")

    def open_application(self, command):
        """Opens an application or brings it to the foreground if already running."""
        app_name = command.replace("open ", "").replace("app", "").replace("application", "").strip().lower()

        # Check if the application is in the common applications dictionary
        if app_name in self.common_applications:
            app_executable = self.common_applications[app_name]

            # Check if the application is running
            pid = self.is_application_running(app_executable)
            if pid:
                speak(f"{app_name} is already running. Bringing it to the foreground.")
                if not self.bring_to_foreground(app_name):
                    speak(f"Could not bring {app_name} to the foreground. It might be minimized or hidden.")
                return

            # If not running, open the application
            try:
                speak(f"Opening {app_name}.")
                subprocess.Popen(app_executable)
            except Exception as e:
                speak(f"Sorry, I couldn't open {app_name}. Please make sure it is installed.")
                print(f"Error: {e}")
        else:
            speak("I'm sorry, I don't recognize that application. Please make sure it is installed and try again.")

    def is_application_running(self, app_name):
        """Checks if a given application is running."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                return proc.pid  # Return the PID of the running process
        return None

    def bring_to_foreground(self, app_name):
        """Brings the application's main window to the foreground."""
        try:
            # Use pywinauto's Desktop object to find windows
            desktop = Desktop(backend="uia")
            windows = [win for win in desktop.windows() if app_name.lower() in win.window_text().lower()]
            
            if windows:
                # Activate the first matching window
                windows[0].set_focus()
                return True
            else:
                print(f"No window found for {app_name}.")
        except Exception as e:
            print(f"Error bringing {app_name} to foreground: {e}")
        return False

    def get_response(self):
        """Prompts the user for a response and retries if no response is detected.
        This method now sets a class flag to prevent other threads from interfering."""
        # Set the flag to indicate we're waiting for a response
        self.waiting_for_response = True
        
        # First, wait until any previous speech has finished
        while speaking:
            time.sleep(0.2)
        
        # Try to access the GUI to set the waiting flag
        try:
            # Look for the gui_instance in the imported modules
            import sys
            for module_name, module in sys.modules.items():
                if 'gui' in module_name and hasattr(module, 'gui_instance'):
                    if module.gui_instance and hasattr(module.gui_instance, 'waiting_for_response'):
                        module.gui_instance.waiting_for_response = True
                    break
        except Exception as e:
            print(f"Note: Could not set GUI waiting flag: {e}")
        
        # Then listen for the response
        response = listen()
        
        # Try to reset the GUI waiting flag
        try:
            import sys
            for module_name, module in sys.modules.items():
                if 'gui' in module_name and hasattr(module, 'gui_instance'):
                    if module.gui_instance and hasattr(module.gui_instance, 'waiting_for_response'):
                        module.gui_instance.waiting_for_response = False
                    break
        except Exception as e:
            print(f"Note: Could not reset GUI waiting flag: {e}")
        
        # If no response detected, try once more
        if response is None:
            speak("I didn't hear you. Could you please repeat?")
            # Wait for speech to complete before listening again
            while speaking:
                time.sleep(0.2)
            response = listen()
        
        # Convert spoken number words to digits if response is a number word
        if response:
            response = self.convert_spoken_numbers_to_digits(response)
        
        # Reset the waiting flag
        self.waiting_for_response = False
        
        return response

    def convert_spoken_numbers_to_digits(self, text):
        """Convert spoken number words to digits."""
        if not text:
            return text
            
        # Dictionary mapping number words to digits
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20',
            'thirty': '30', 'forty': '40', 'fifty': '50',
            'sixty': '60', 'seventy': '70', 'eighty': '80', 'ninety': '90'
        }
        
        # If text is just a single number word
        if text.lower() in number_words:
            return number_words[text.lower()]
        
        # For compound numbers like "twenty three"
        for word, digit in number_words.items():
            if text.lower() == word:
                return digit
        
        # Handle cases like "twenty one" -> "21"
        for tens_word in ['twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']:
            if text.lower().startswith(tens_word + " "):
                # Get the rest of the string after the tens word
                ones_word = text.lower().replace(tens_word + " ", "").strip()
                # If the rest is a single digit number word
                if ones_word in number_words and len(number_words[ones_word]) == 1:
                    tens_digit = number_words[tens_word][0]  # First digit of the tens
                    ones_digit = number_words[ones_word]
                    return tens_digit + ones_digit
        
        return text

    def search_google(self):
        """Start a conversation to get search terms"""
        speak("What would you like to search?")
        response = self.get_response()
        if response:
            self.search_google_with_term(response)

    def play_youtube_video(self):
        """Start a conversation to get YouTube search terms"""
        speak("What would you like to watch?")
        response = self.get_response()
        if response:
            self.play_youtube_with_term(response)

    # Email commands
    def send_email(self):
        """Guides the user through composing and sending an email."""
        # Check if email credentials are stored
        email_address = self.get_email_credentials()
        if not email_address:
            return

        # Get recipient's email address
        recipient_confirmed = False
        to_email = None
        
        # First try with voice input
        speak("Who would you like to email? Please say their email address.")
        to_email = self.get_response()
        
        if to_email and '@' in to_email:
            speak(f"I heard {to_email}. Is this correct? Please say yes or no.")
            confirmation = self.get_response()
            
            if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                recipient_confirmed = True
        
        # If voice didn't work, fall back to typing
        if not recipient_confirmed:
            speak("Let's try typing the email address instead.")
            while not recipient_confirmed:
                print("Enter recipient's email address: ", end="")
                to_email = input().strip()
                
                if not to_email or '@' not in to_email:
                    speak("That doesn't seem to be a valid email address. Please try again.")
                    continue
                    
                # Confirm the recipient email is correct
                speak(f"I see you entered {to_email}. Is this correct? Please say yes or no.")
                confirmation = self.get_response()
                
                if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                    recipient_confirmed = True
                else:
                    speak("Let's try again.")

        # Get email subject
        subject_confirmed = False
        subject = None
        
        while not subject_confirmed:
            speak("What's the subject of your email?")
            subject = self.get_response()
            
            if not subject:
                speak("I didn't catch that. Let's try again.")
                continue
                
            # Confirm the subject is correct
            speak(f"The subject will be: {subject}. Is this correct? Please say yes or no.")
            confirmation = self.get_response()
            
            if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                subject_confirmed = True
            else:
                speak("Let's try again.")

        # Get email content
        speak("Please dictate the content of your email. Say 'stop' when you're finished.")
        email_content = []
        while True:
            content = self.get_response()
            if content and "stop" in content.lower():
                break
            elif content:
                email_content.append(content)
                # Provide feedback that the content was captured
                speak("Got it. Continue or say 'stop' when finished.")

        if not email_content:
            speak("No content was provided. Email cancelled.")
            return

        # Prepare email text
        email_text = " ".join(email_content)
        
        # Provide a summary of the email
        speak("Here's a summary of your email:")
        speak(f"To: {to_email}")
        speak(f"Subject: {subject}")
        speak("Content preview: " + (email_text[:100] + "..." if len(email_text) > 100 else email_text))
        
        # Confirm before sending
        speak("Would you like to send this email now? Say yes or no.")
        confirmation = self.get_response()
        
        if confirmation and "yes" in confirmation.lower():
            try:
                # Determine email provider from address
                provider = self.detect_email_provider(email_address)
                if not provider:
                    speak("Could not determine your email provider. Please check your email settings.")
                    return
                
                # Password will be retrieved from config file
                password = None
                
                # Send the email
                self.send_smtp_email(email_address, to_email, subject, email_text, provider, password)
                speak("Email sent successfully.")
            except Exception as e:
                speak("Sorry, I encountered an error while sending your email.")
                print(f"Email error: {e}")
        else:
            speak("Email sending cancelled.")

    def get_email_credentials(self):
        """Gets the email credentials, asking user to input them if not already saved."""
        config_file = "email_config.json"
        
        # Check if config file exists and has valid data
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                
                email = config.get("email")
                # Check if the config has been properly set up
                if email and "@" in email and email != "your_email@example.com":
                    return email
            except:
                # If there's any error reading the file, we'll create a new one
                pass
        
        # If we get here, we need to ask for credentials
        speak("I need your email address to send emails. Please say your email address.")
        email_confirmed = False
        
        # First try voice input
        email = self.get_response()
        if email and "@" in email:
            speak(f"I heard {email}. Is this correct? Please say yes or no.")
            confirmation = self.get_response()
            
            if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                email_confirmed = True
        
        # If voice input didn't work, fall back to typing
        if not email_confirmed:
            speak("Let's try typing your email address instead.")
            while not email_confirmed:
                print("Enter your email address: ", end="")
                email = input().strip()
                
                if not email or "@" not in email:
                    speak("That doesn't seem to be a valid email address. Let's try again.")
                    continue
                
                # Confirm the email is correct
                speak(f"I see you entered {email}. Is this correct? Please say yes or no.")
                confirmation = self.get_response()
                
                if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                    email_confirmed = True
                else:
                    speak("Let's try again.")
        
        speak("Now I need your email password or app password. This will be saved securely.")
        speak("For services like Gmail, you may need to create an app password.")
        print("Enter your password (will not be displayed): ", end="")
        password = getpass.getpass("")
        
        if not password:
            speak("No password entered. Email setup cancelled.")
            return None
        
        # Save the credentials
        config = {
            "email": email,
            "password": base64.b64encode(password.encode()).decode()  # Basic obfuscation
        }
        
        try:
            with open(config_file, "w") as f:
                json.dump(config, f)
            speak("Email credentials saved successfully.")
        except Exception as e:
            speak("There was an error saving your credentials.")
            print(f"Error: {e}")
            return None
        
        return email

    def change_email_settings(self):
        """Allows the user to change their saved email credentials."""
        speak("Let's update your email settings. Do you want to change your email address, password, or both?")
        response = self.get_response()
        
        if not response:
            speak("I didn't catch that. Email settings update cancelled.")
            return
        
        config_file = "email_config.json"
        config = {}
        
        # Try to load existing config
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
            except:
                # If there's an error reading, we'll start fresh
                pass
        
        # Update email if requested
        if "email" in response.lower() or "both" in response.lower():
            email_confirmed = False
            
            # First try voice input
            speak("Please say your new email address.")
            email = self.get_response()
            
            if email and "@" in email:
                speak(f"I heard {email}. Is this correct? Please say yes or no.")
                confirmation = self.get_response()
                
                if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                    config["email"] = email
                    speak("Email address updated.")
                    email_confirmed = True
            
            # If voice didn't work, fall back to typing
            if not email_confirmed:
                speak("Let's try typing your email address instead.")
                while not email_confirmed:
                    print("Enter your new email address: ", end="")
                    email = input().strip()
                    
                    if not email or "@" not in email:
                        speak("That doesn't seem to be a valid email address. Let's try again.")
                        continue
                    
                    # Confirm the email is correct
                    speak(f"I see you entered {email}. Is this correct? Please say yes or no.")
                    confirmation = self.get_response()
                    
                    if confirmation and ("yes" in confirmation.lower() or "correct" in confirmation.lower()):
                        config["email"] = email
                        speak("Email address updated.")
                        email_confirmed = True
                    else:
                        speak("Let's try again.")
        
        # Update password if requested
        if "password" in response.lower() or "both" in response.lower():
            speak("Please type your new password.")
            print("Enter your new password (will not be displayed): ", end="")
            password = getpass.getpass("")
            
            if not password:
                speak("No password entered.")
            else:
                # Confirm the password was entered correctly
                speak("To confirm, please type your password again.")
                print("Confirm your password (will not be displayed): ", end="")
                confirm_password = getpass.getpass("")
                
                if password == confirm_password:
                    config["password"] = base64.b64encode(password.encode()).decode()
                    speak("Password updated successfully.")
                else:
                    speak("Passwords do not match. Password not updated.")
        
        # Save the updated config
        try:
            with open(config_file, "w") as f:
                json.dump(config, f)
            speak("Email settings updated successfully.")
        except Exception as e:
            speak("There was an error saving your settings.")
            print(f"Error: {e}")

    def detect_email_provider(self, email):
        """Detects the email provider based on the email address."""
        if "@gmail" in email:
            return "gmail"
        elif "@outlook" in email or "@hotmail" in email or "@live" in email:
            return "outlook"  
        elif "@yahoo" in email:
            return "yahoo"
        else:
            # Generic approach - ask user
            speak("I don't recognize your email provider. Please tell me which provider you use: gmail, outlook, or yahoo.")
            provider = self.get_response()
            if provider and provider.lower() in self.smtp_configs:
                return provider.lower()
            return None

    def send_smtp_email(self, from_email, to_email, subject, body, provider, password=None):
        """Sends an email using SMTP protocol."""
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Get SMTP server details
        smtp_info = self.smtp_configs.get(provider)
        if not smtp_info:
            raise ValueError(f"No SMTP configuration found for {provider}")
            
        # Get password from config if not provided
        if password is None:
            try:
                with open("email_config.json", "r") as f:
                    config = json.load(f)
                password = base64.b64decode(config.get("password").encode()).decode()
            except Exception as e:
                raise ValueError(f"Could not retrieve password from config: {e}")
            
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_info['server'], smtp_info['port'])
        server.starttls()  # Secure the connection
        
        try:
            # Login
            server.login(from_email, password)
            
            # Send email
            server.send_message(msg)
            print("Email sent successfully")
        finally:
            server.quit()

    # Weather commands that use the WeatherService class
    def set_weather_location(self):
        """Sets the default location for weather queries."""
        speak("What city would you like to set as your default weather location?")
        location = self.get_response()
        
        if not location:
            speak("I couldn't understand the location. Default location not set.")
            return
        
        # Use the weather service to set the location
        success = self.weather_service.set_location(location)
        if success:
            speak(f"I've set {location} as your default weather location.")
        else:
            speak("There was an error setting your default location.")

    def set_weather_api_key(self):
        """Sets the OpenWeatherMap API key."""
        speak("Please enter your OpenWeatherMap API key.")
        print("Enter your API key: ", end="")
        api_key = input().strip()
        
        if not api_key:
            speak("No API key provided. Weather functionality will be limited.")
            return
        
        # Use the weather service to set the API key
        success = self.weather_service.set_api_key(api_key)
        if success:
            speak("API key verified and saved successfully. You can now use weather functions.")
        else:
            speak("There was an error saving your API key.")

    def get_current_weather(self):
        """Gets the current weather using the WeatherService."""
        # Get the weather data from the weather service
        weather_data = self.weather_service.get_weather()
        
        if weather_data["success"]:
            # Extract and report weather data
            location = weather_data["location"]
            temperature = weather_data["temperature"]
            condition = weather_data["description"]
            humidity = weather_data["humidity"]
            wind_speed = weather_data["wind_speed"]
            
            # Provide comprehensive weather information
            speak(f"Current weather in {location}:")
            speak(f"Temperature is {temperature} degrees Celsius")
            speak(f"Condition: {condition}")
            speak(f"Humidity: {humidity}%")
            speak(f"Wind speed: {wind_speed} meters per second")
            
            # Get forecast information
            forecast_data = self.weather_service.get_forecast()
            if forecast_data["success"]:
                # Add information about rain and temperature range
                if forecast_data["rain_expected"]:
                    speak("There is a chance of rain today.")
                speak(f"Today's temperatures will range from {forecast_data['min_temp']} to {forecast_data['max_temp']} degrees Celsius.")
        else:
            if "No API key configured" in weather_data.get("error", ""):
                speak("You need to set up an OpenWeatherMap API key first. Say 'set weather API' to do this.")
            else:
                speak(f"Sorry, I couldn't retrieve weather information. {weather_data.get('error', 'Unknown error')}")

    # Alarm commands that use the AlarmClock class
    def set_alarm(self):
        """Sets an alarm for a specific time by asking for hour and minute separately."""
        # Ask for the hour first
        speak("What hour would you like to set the alarm for? Please say a number between 0 and 23.")
        hour_input = self.get_response()
        
        if not hour_input:
            speak("I didn't catch that. Alarm setting cancelled.")
            return
        
        # Try to parse the hour
        try:
            hours = int(hour_input.strip())
            if not (0 <= hours <= 23):
                speak("That doesn't seem to be a valid hour. Hour must be between 0 and 23. Alarm setting cancelled.")
                return
        except ValueError:
            speak("I couldn't understand that as a valid hour. Alarm setting cancelled.")
            return
        
        # Now ask for the minute
        speak("What minute would you like to set the alarm for? Please say a number between 0 and 59.")
        minute_input = self.get_response()
        
        if not minute_input:
            speak("I didn't catch that. Alarm setting cancelled.")
            return
        
        # Try to parse the minute
        try:
            minutes = int(minute_input.strip())
            if not (0 <= minutes <= 59):
                speak("That doesn't seem to be a valid minute. Minute must be between 0 and 59. Alarm setting cancelled.")
                return
        except ValueError:
            speak("I couldn't understand that as a valid minute. Alarm setting cancelled.")
            return
        
        # Confirm the time with the user
        speak(f"I'll set an alarm for {hours:02d}:{minutes:02d}. Is this correct? Please say yes or no.")
        confirmation = self.get_response()
        
        if not confirmation or "yes" not in confirmation.lower():
            speak("Alarm setting cancelled.")
            return
        
        # Ask for which days
        speak("For which days? Say 'everyday', 'weekdays', 'weekends', or specific days like 'Monday, Wednesday, Friday'.")
        days_input = self.get_response()
        
        if not days_input:
            days_input = "everyday"  # Default
            speak("I'll set the alarm for everyday.")
        
        # Set the alarm using the alarm clock
        success = self.alarm_clock.set_alarm(hours, minutes, days_input)
        
        if not success:
            speak("There was an error setting the alarm. Please try again.")

    def remove_alarm(self):
        """Removes a specific alarm by asking for hour and minute separately."""
        # First list the alarms
        alarms = self.alarm_clock.list_alarms()
        
        if not self.alarm_clock.alarms:
            return  # No alarms to remove
        
        # Ask for the hour first
        speak("What hour is the alarm you want to remove? Please say a number between 0 and 23.")
        hour_input = self.get_response()
        
        if not hour_input:
            speak("I didn't catch that. Alarm removal cancelled.")
            return
        
        # Try to parse the hour
        try:
            hours = int(hour_input.strip())
            if not (0 <= hours <= 23):
                speak("That doesn't seem to be a valid hour. Hour must be between 0 and 23. Alarm removal cancelled.")
                return
        except ValueError:
            speak("I couldn't understand that as a valid hour. Alarm removal cancelled.")
            return
        
        # Now ask for the minute
        speak("What minute is the alarm you want to remove? Please say a number between 0 and 59.")
        minute_input = self.get_response()
        
        if not minute_input:
            speak("I didn't catch that. Alarm removal cancelled.")
            return
        
        # Try to parse the minute
        try:
            minutes = int(minute_input.strip())
            if not (0 <= minutes <= 59):
                speak("That doesn't seem to be a valid minute. Minute must be between 0 and 59. Alarm removal cancelled.")
                return
        except ValueError:
            speak("I couldn't understand that as a valid minute. Alarm removal cancelled.")
            return
        
        # Confirm with the user
        speak(f"I'll remove the alarm for {hours:02d}:{minutes:02d}. Is this correct? Please say yes or no.")
        confirmation = self.get_response()
        
        if not confirmation or "yes" not in confirmation.lower():
            speak("Alarm removal cancelled.")
            return
        
        # Remove the alarm using the alarm clock
        success = self.alarm_clock.remove_alarm(hours, minutes)
        
        if not success:
            speak("There was an error removing the alarm. Please check the time and try again.")

    def list_alarms(self):
        """Lists all active alarms."""
        # Use the alarm clock to list alarms
        self.alarm_clock.list_alarms()  # This method already includes speaking the alarms

    # Facial recognition methods
    def add_face_user(self):
        """Adds a new user face to the recognition system."""
        if not self.facial_recognition_available or self.face_recognizer is None:
            speak("Facial recognition is not available. Please check if OpenCV is installed correctly.")
            return
            
        # Check if camera is available
        try:
            if not self.face_recognizer.is_camera_available():
                speak("I don't detect a camera on your system. Please check your camera connection.")
                return
        except Exception as e:
            print(f"Error checking camera availability: {e}")
            speak("There was an error checking camera availability.")
            return
            
        try:
            self.face_recognizer.add_new_user()
        except Exception as e:
            print(f"Error in add_face_user: {e}")
            speak("I encountered an error while trying to add a new user.")

    def list_face_users(self):
        """Lists all registered face users."""
        if not self.facial_recognition_available or self.face_recognizer is None:
            speak("Facial recognition is not available.")
            return
            
        try:
            self.face_recognizer.list_users()
        except Exception as e:
            print(f"Error in list_face_users: {e}")
            speak("I encountered an error while trying to list users.")

    def remove_face_user(self):
        """Removes a user from the face recognition system."""
        if not self.facial_recognition_available or self.face_recognizer is None:
            speak("Facial recognition is not available.")
            return
            
        speak("Which user would you like to remove?")
        response = self.get_response()
        
        if response:
            try:
                self.face_recognizer.remove_user(response)
            except Exception as e:
                print(f"Error in remove_face_user: {e}")
                speak("I encountered an error while trying to remove the user.")
        else:
            speak("I didn't catch that name. Please try again.")

    def recognize_face(self):
        """Activates facial recognition to identify the current user."""
        if not self.facial_recognition_available or self.face_recognizer is None:
            speak("Facial recognition is not available.")
            return
            
        # Check if camera is available
        try:
            if not self.face_recognizer.is_camera_available():
                speak("I don't detect a camera on your system. Please check your camera connection.")
                return
        except Exception as e:
            print(f"Error checking camera availability: {e}")
            speak("There was an error checking camera availability.")
            return
            
        speak("Looking for faces to recognize...")
        try:
            self.face_recognizer.start_recognition()
        except Exception as e:
            print(f"Error in recognize_face: {e}")
            speak("I encountered an error during facial recognition.")