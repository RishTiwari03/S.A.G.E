# __init__.py
# This file makes the assistant directory a Python package

# Import modules that are essential first
from . import text_to_speech
from . import voice_recognition
from . import weather_service
from . import alarm_clock

# Try to import OpenCV-based facial recognition
try:
    import cv2
    print("OpenCV imported successfully. Using full facial recognition.")
    try:
        from . import facial_recognition
    except ImportError:
        print("Facial recognition module not available. Using simplified version.")
        from . import facial_recognition_simple as facial_recognition
    except Exception as e:
        print(f"Error importing facial recognition: {e}. Using simplified version.")
        from . import facial_recognition_simple as facial_recognition
except ImportError:
    print("OpenCV (cv2) not found. Using simplified facial recognition.")
    from . import facial_recognition_simple as facial_recognition
except Exception as e:
    print(f"Error importing OpenCV: {e}. Using simplified facial recognition.")
    from . import facial_recognition_simple as facial_recognition

# Try to import camera utilities
try:
    from . import camera_utils_debug
except ImportError:
    print("Camera utilities module not available.")
except Exception as e:
    print(f"Error importing camera utilities: {e}")

# Import core and commands last, as they may depend on the other modules
from . import core
from . import commands