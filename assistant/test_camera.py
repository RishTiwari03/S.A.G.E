# test_camera.py
# Standalone script to test camera access

import cv2
import platform
import sys
import time

def test_camera():
    """Simple test to see if camera works"""
    print(f"OpenCV version: {cv2.__version__}")
    print(f"Python version: {sys.version}")
    print(f"Operating system: {platform.system()} {platform.release()}")
    
    print("\nTrying to access camera with default settings...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Failed to open camera!")
        print("Possible reasons:")
        print("1. Camera is being used by another application")
        print("2. Camera drivers are not installed properly")
        print("3. Privacy settings are blocking camera access")
        print("4. No camera is connected to this computer")
        return False
    
    print("Camera opened successfully!")
    print("Trying to read a frame...")
    
    ret, frame = cap.read()
    if not ret:
        print("Failed to read a frame from the camera!")
        cap.release()
        return False
    
    print("Successfully read a frame from the camera!")
    print("Showing camera feed (press 'q' to exit)...")
    
    cv2.namedWindow('Camera Test', cv2.WINDOW_NORMAL)
    
    try:

        start_time = time.time()
        while (time.time() - start_time) < 10:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Display the frame
            cv2.imshow('Camera Test', frame)
            
            # Break loop if 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("Camera test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during camera test: {e}")
        try:
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass
        return False

if __name__ == "__main__":
    print("===== CAMERA TEST =====")
    result = test_camera()
    
    if result:
        print("\nSUCCESS: Your camera is working properly!")
    else:
        print("\nFAILED: Your camera is not working properly.")
        
        if platform.system() == "Windows":
            print("\nTo check Windows camera privacy settings:")
            print("1. Go to Start > Settings > Privacy > Camera")
            print("2. Make sure 'Allow apps to access your camera' is ON")
            print("3. Make sure 'Allow desktop apps to access your camera' is ON")
        
        print("\nOther troubleshooting steps:")
        print("1. Close any applications that might be using the camera")
        print("2. Restart your computer")
        print("3. Check if your camera is properly connected")
        print("4. Update your camera drivers")