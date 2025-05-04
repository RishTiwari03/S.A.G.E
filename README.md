# S.A.G.E - Smart Assistant for General Environments

SAGE is an intelligent desktop assistant designed to enhance productivity with voice commands, facial recognition, and various utility services. Built in Python, SAGE provides a comprehensive interface for both terminal and GUI interactions.

## Features

- **Voice Recognition**: Respond to spoken commands and queries
- **Text-to-Speech**: Provide audible responses with natural voice output
- **Facial Recognition**: Identify users and personalize interactions (requires OpenCV)
- **Weather Services**: Fetch current weather and forecasts
- **Alarm System**: Set and manage alarms with custom schedules
- **Email Functionality**: Compose and send emails through voice commands
- **Application Control**: Open and manage desktop applications
- **Web Navigation**: Search Google, YouTube, and open websites through voice
- **System Controls**: Adjust volume and other system settings

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/RishTiwari03/S.A.G.E.git
   cd S.A.G.E
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Optional: Install OpenCV for facial recognition features:
   ```
   pip install opencv-python
   ```

## Usage

### GUI Mode (Recommended)

Run the GUI version of SAGE:
```
python start_sage_gui.py
```

### Terminal Mode

Run SAGE in terminal mode:
```
python main.py
```

### Test Camera Setup

If you're experiencing issues with the camera (for facial recognition):
```
python test_camera.py
```

## Configuration

- **Weather Service**: Set your OpenWeatherMap API key with the command "set weather api"
- **Email**: Configure your email settings with "send email" or "change email settings"
- **Facial Recognition**: Add your face with "add face" command

## Voice Commands

- "Open [application/website]" - Opens the specified application or website
- "Search for [query]" - Searches Google for the specified query
- "Play video for [query]" - Searches YouTube for videos
- "Get weather" - Provides current weather information
- "Set alarm" - Creates a new alarm
- "Add face" - Registers a new user for facial recognition
- "Recognize face" - Identifies the current user using facial recognition
- "Increase/decrease volume" - Adjusts system volume
- "Send email" - Starts the email composition process
- "Wake up" - Activates the assistant from sleep mode
- "Mute" - Puts the assistant in sleep mode

## Directory Structure

- `/assistant` - Core assistant modules
- `/gui` - GUI implementation files
- `/faces_data` - Storage for facial recognition data (generated when used)

## Requirements

See requirements.txt for a complete list of dependencies.
Main dependencies include:
- speech_recognition
- pyttsx3
- opencv-python (optional, for facial recognition)
- requests (for weather services)
- numpy
- pywin32 (Windows only)
- tkinter (for GUI)

## License

[Your license here]

## Contributors

- RishTiwari03