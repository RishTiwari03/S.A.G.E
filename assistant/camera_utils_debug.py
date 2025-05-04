# camera_utils_debug.py

import cv2
import platform
import subprocess
import time
import sys
import os
from assistant.text_to_speech import speak

def debug_camera_info():
    """Print detailed camera and OpenCV information for debugging"""
    print("\n----- CAMERA DEBUGGING INFORMATION -----")
    print(f"OpenCV version: {cv2.__version__}")
    print(f"Python version: {sys.version}")
    print(f"Operating system: {platform.system()} {platform.release()}")
    
    # Check camera backends available in this OpenCV build
    backends = []
    if hasattr(cv2, 'CAP_DSHOW'):
        backends.append("DirectShow")
    if hasattr(cv2, 'CAP_MSMF'):
        backends.append("Microsoft Media Foundation")
    if hasattr(cv2, 'CAP_AVFOUNDATION'):
        backends.append("AVFoundation (macOS)")
    if hasattr(cv2, 'CAP_V4L2'):
        backends.append("Video4Linux2")
    
    print(f"Available camera backends: {', '.join(backends)}")
    
    # Try to detect connected cameras (Windows-specific)
    if platform.system() == "Windows":
        try:
            # This only works on Windows with the right permissions
            output = subprocess.check_output("wmic path CIM_LogicalDevice where \"Description like '%camera%'\" get Caption", shell=True)
            cameras = output.decode().strip().split('\n')[1:]
            print(f"Detected cameras via WMI: {cameras}")
        except Exception as e:
            print(f"Error detecting cameras via WMI: {e}")
    
    print("----- END DEBUGGING INFORMATION -----\n")

def test_camera_with_simple_window():
    """Test if camera works by showing a simple window with camera feed"""
    print("Testing camera with a simple window...")
    try:
        # Try camera index 0 with default backend
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Failed to open camera with default backend")
            speak("I couldn't access your camera with the default settings.")
            return False
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to read a frame from camera")
            cap.release()
            speak("Your camera opened but I couldn't read any frames from it.")
            return False
        
        # Show camera feed in window
        window_name = 'Camera Test (Press any key to close)'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, frame)
        speak("I opened a window to test your camera. You should see yourself. Press any key to close it.")
        
        # Wait for a key press
        cv2.waitKey(0)
        
        # Clean up
        cv2.destroyWindow(window_name)
        cap.release()
        return True
        
    except Exception as e:
        print(f"Error testing camera: {e}")
        speak("There was an error testing your camera.")
        return False

def test_camera_access():
    """Test if camera is accessible and return recommended capture method"""
    debug_camera_info()
    
    os_name = platform.system()
    print(f"Operating system: {os_name}")
    
    # First try the simplest approach to see if we have basic camera access
    result = test_camera_with_simple_window()
    if result:
        print("Basic camera test succeeded!")
    else:
        print("Basic camera test failed.")
    
    camera_capture_methods = []
    
    # Based on OS, determine what capture methods to try
    if os_name == "Windows":
        camera_capture_methods = [
            {"index": 0, "api": cv2.CAP_DSHOW, "name": "DirectShow"},
            {"index": 0, "api": cv2.CAP_MSMF, "name": "Microsoft Media Foundation"},
            {"index": 0, "api": None, "name": "Default"}
        ]
    elif os_name == "Darwin":  # macOS
        camera_capture_methods = [
            {"index": 0, "api": cv2.CAP_AVFOUNDATION, "name": "AVFoundation"},
            {"index": 0, "api": None, "name": "Default"}
        ]
    else:  # Linux and others
        camera_capture_methods = [
            {"index": 0, "api": cv2.CAP_V4L2, "name": "V4L2"},
            {"index": 0, "api": None, "name": "Default"}
        ]
    
    # Try all camera indices from 0 to 2
    for index in range(3):
        for method in camera_capture_methods:
            method_copy = method.copy()
            method_copy["index"] = index
            camera_capture_methods.append(method_copy)
    
    # Test each method
    for method in camera_capture_methods:
        try:
            print(f"Trying camera index {method['index']} with {method['name']} backend...")
            
            if method["api"] is None:
                cap = cv2.VideoCapture(method["index"])
            else:
                cap = cv2.VideoCapture(method["index"], method["api"])
                
            if cap.isOpened():
                # Try to read a frame to make sure it's actually working
                ret, frame = cap.read()
                if ret:
                    cap.release()
                    print(f"Successfully accessed camera with {method['name']} backend and index {method['index']}")
                    return {
                        "success": True,
                        "index": method["index"],
                        "api": method["api"]
                    }
                else:
                    print(f"Camera opened but couldn't read frames with {method['name']} backend")
                    cap.release()
            else:
                print(f"Failed to open camera with {method['name']} backend")
        except Exception as e:
            print(f"Error with {method['name']} backend: {e}")
    
    # If we get here, all methods failed
    return {
        "success": False,
        "error": "Could not access any camera with any method"
    }

def get_camera_capture(with_retry=True):
    """Try to get a working camera capture object, with diagnostics for failures"""
    camera_test = test_camera_access()
    
    if camera_test["success"]:
        # Use the successful method
        if camera_test["api"] is None:
            cap = cv2.VideoCapture(camera_test["index"])
        else:
            cap = cv2.VideoCapture(camera_test["index"], camera_test["api"])
        
        return {
            "success": True,
            "capture": cap
        }
    else:
        # All methods failed, provide troubleshooting help
        
        if platform.system() == "Windows":
            # Check if privacy settings are blocking camera access
            speak("I couldn't access your camera. This might be due to Windows privacy settings or the camera being used by another application.")
            speak("Would you like me to help you check your camera settings?")
            print("Enter yes or no: ", end="")
            response = input().strip().lower()
            
            if response == "yes":
                # Open Windows camera privacy settings
                try:
                    subprocess.run(['start', 'ms-settings:privacy-webcam'], shell=True)
                    speak("I've opened the Windows camera privacy settings. Please make sure camera access for desktop apps is enabled.")
                    time.sleep(5)  # Give user time to change settings
                    
                    if with_retry:
                        speak("Let's try accessing the camera again.")
                        return get_camera_capture(with_retry=False)  # Try one more time
                except Exception as e:
                    print(f"Error opening settings: {e}")
        else:
            speak("I couldn't access your camera. Please check that your camera is connected properly and not being used by another application.")
        
        return {
            "success": False,
            "error": "Camera access failed after troubleshooting attempts"
        }

def safe_release_camera(cap):
    """Safely release the camera capture"""
    try:
        if cap is not None and cap.isOpened():
            cap.release()
            return True
    except Exception as e:
        print(f"Error releasing camera: {e}")
    return False