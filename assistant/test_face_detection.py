# test_face_detection.py
# Standalone script to test face detection

import cv2
import os
import sys
import time

def test_face_detection():
    """Test if face detection works with your camera"""
    print("Testing face detection with OpenCV...")
    
    # Check if OpenCV has the face detection file
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    if not os.path.exists(cascade_path):
        print(f"Error: Face detection file not found at {cascade_path}")
        print("This may indicate an issue with your OpenCV installation.")
        return False
    
    # Load the face detector
    try:
        face_detector = cv2.CascadeClassifier(cascade_path)
    except Exception as e:
        print(f"Error loading face detector: {e}")
        return False
    
    print("Face detector loaded successfully.")
    print("Trying to access camera...")
    
    # Try all possible camera indices
    camera_opened = False
    cap = None
    
    for camera_index in range(3):  # Try indices 0, 1, 2
        try:
            print(f"Trying camera index {camera_index}...")
            
            # Try with DirectShow on Windows
            if hasattr(cv2, 'CAP_DSHOW'):
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret:
                        print(f"Camera opened successfully with index {camera_index} and DirectShow")
                        camera_opened = True
                        break
                    else:
                        print("Camera opened but couldn't read frames")
                        cap.release()
                
            # Try with default backend
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret:
                    print(f"Camera opened successfully with index {camera_index} and default backend")
                    camera_opened = True
                    break
                else:
                    print("Camera opened but couldn't read frames")
                    cap.release()
        except Exception as e:
            print(f"Error with camera index {camera_index}: {e}")
    
    if not camera_opened:
        print("Failed to open any camera. Face detection test aborted.")
        return False
    
    print("Camera opened successfully.")
    print("Starting face detection (press 'q' to exit)...")
    
    cv2.namedWindow('Face Detection Test', cv2.WINDOW_NORMAL)
    
    try:
        # Show camera feed with face detection for 20 seconds or until 'q' is pressed
        start_time = time.time()
        face_detected = False
        
        while (time.time() - start_time) < 20:
            ret, frame = cap.read()
            if not ret:
                print("Error reading frame from camera")
                break
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangles around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                face_detected = True
            
            # Add face detection status text
            status_text = "Status: Face detected" if face_detected else "Status: No face detected"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Show frame count and time elapsed
            frame_info = f"Time: {int(time.time() - start_time)}s"
            cv2.putText(frame, frame_info, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display the frame
            cv2.imshow('Face Detection Test', frame)
            
            # Break loop if 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
        if face_detected:
            print("Success! Face detection is working properly.")
            return True
        else:
            print("No faces were detected during the test.")
            print("This could be because:")
            print("1. No one was in front of the camera")
            print("2. Lighting conditions were poor")
            print("3. Face was not positioned properly")
            print("4. There's an issue with face detection")
            return False
        
    except Exception as e:
        print(f"Error during face detection test: {e}")
        try:
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass
        return False

if __name__ == "__main__":
    print("===== FACE DETECTION TEST =====")
    result = test_face_detection()
    
    if result:
        print("\nSUCCESS: Face detection is working properly!")
    else:
        print("\nWARNING: Face detection test completed, but some issues were encountered.")
        print("See above for details and troubleshooting suggestions.")