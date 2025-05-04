# facial_recognition.py

import cv2
import os
import numpy as np
import pickle
import time
import threading
import platform
from assistant.text_to_speech import speak

class FacialRecognizer:
    def __init__(self):
        # Path to save faces data
        self.data_dir = "faces_data"
        self.model_path = os.path.join(self.data_dir, "face_model.pkl")
        self.labels_path = os.path.join(self.data_dir, "face_labels.pkl")
        
        # Ensure the directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Initialize empty labels dict to avoid attribute errors
        self.labels = {}
            
        # Initialize OpenCV face detector and recognizer
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Track recognized users in the current session
        self.recognized_users = set()
        self.is_running = False
        self.recognition_thread = None
        
        # Load existing models if available
        self.load_model()
    
    def is_camera_available(self):
        """Check if a camera is available on the system"""
        try:
            # Try to open the camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Camera could not be opened.")
                return False
                
            # Try to read a frame
            ret, frame = cap.read()
            
            # Clean up
            cap.release()
            
            if not ret:
                print("Could not read frame from camera.")
                return False
                
            return True
        except Exception as e:
            print(f"Error checking camera availability: {e}")
            return False
    
    def load_model(self):
        """Load existing face recognition model and labels if available"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.labels_path):
                self.face_recognizer.read(self.model_path)
                with open(self.labels_path, 'rb') as f:
                    self.labels = pickle.load(f)
                print(f"Loaded face recognition model with {len(self.labels)} users")
                return True
            else:
                print("No existing face recognition model found")
                self.labels = {}
                return False
        except Exception as e:
            print(f"Error loading face recognition model: {e}")
            self.labels = {}
            return False
    
    def save_model(self):
        """Save the current face recognition model and labels"""
        try:
            self.face_recognizer.write(self.model_path)
            with open(self.labels_path, 'wb') as f:
                pickle.dump(self.labels, f)
            print(f"Saved face recognition model with {len(self.labels)} users")
            return True
        except Exception as e:
            print(f"Error saving face recognition model: {e}")
            return False
    
    def detect_faces(self, frame):
        """Detect faces in the given frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5,
            minSize=(30, 30)
        )
        return gray, faces
    
    def add_new_user(self):
        """Add a new user to the face recognition model"""
        # Check if labels attribute exists
        if not hasattr(self, 'labels'):
            self.labels = {}
            
        speak("I'll need to take several pictures of your face. What's your name?")
        
        # Simulate getting user's name (in a real implementation, use voice recognition)
        print("Enter your name: ", end="")
        user_name = input().strip()
        
        if not user_name:
            speak("I didn't get a name. User registration cancelled.")
            return False
        
        # Check if the user already exists
        for user_id, name in self.labels.items():
            if name.lower() == user_name.lower():
                speak(f"A user named {user_name} already exists. Do you want to update their face data?")
                print("Enter yes or no: ", end="")
                response = input().strip().lower()
                if response != "yes":
                    speak("User registration cancelled.")
                    return False
                # If updating, use the same user ID
                new_user_id = user_id
                break
        else:
            # Create a new user ID
            new_user_id = len(self.labels) + 1
        
        speak(f"Hello {user_name}. I'm going to take 20 pictures of your face. Please look at the camera and move your head slightly between shots.")
        
        # Try different camera indices and backends
        camera_opened = False
        cap = None
        
        # Try different camera indices (0, 1, 2)
        for camera_index in range(3):
            try:
                # Try DirectShow backend first (more reliable on Windows)
                if hasattr(cv2, 'CAP_DSHOW'):
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        ret, test_frame = cap.read()
                        if ret:
                            camera_opened = True
                            print(f"Camera opened successfully with index {camera_index} using DirectShow")
                            break
                
                # Try with default backend
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret:
                        camera_opened = True
                        print(f"Camera opened successfully with index {camera_index} using default backend")
                        break
                    else:
                        print("Camera opened but couldn't read frames")
                        cap.release()
            except Exception as e:
                print(f"Error with camera index {camera_index}: {e}")
        
        if not camera_opened:
            speak("Could not access any camera. Registration failed. Please check your camera connection and permissions.")
            return False
        
        face_samples = []
        sample_count = 0
        
        speak("Starting to capture your face. Please look at the camera and move slightly between captures.")
        time.sleep(1)
        
        # Set a timer for capture pacing
        last_capture_time = time.time()
        capture_interval = 1.0  # Wait 1 second between captures
        
        while sample_count < 20:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Get the current time
            current_time = time.time()
            
            # Display status text on frame
            status_text = f"Capturing image {sample_count+1}/20"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if current_time - last_capture_time >= capture_interval:
                # Time to try a capture
                hint_text = "Hold still for capture..."
                cv2.putText(frame, hint_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Show countdown
                remaining = capture_interval - (current_time - last_capture_time)
                hint_text = f"Next capture in {remaining:.1f}s"
                cv2.putText(frame, hint_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Detect faces
            gray, faces = self.detect_faces(frame)
            
            # Display the frame with face detection rectangles
            face_detected = False
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                face_detected = True
            
            # Display if a face is detected
            if face_detected:
                cv2.putText(frame, "Face detected", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "No face detected", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
            cv2.imshow('Face Registration', frame)
            
            # If there's exactly one face and enough time has passed since last capture, take a sample
            if len(faces) == 1 and (current_time - last_capture_time >= capture_interval):
                x, y, w, h = faces[0]
                face_sample = gray[y:y+h, x:x+w]
                face_samples.append(face_sample)
                sample_count += 1
                last_capture_time = current_time  # Reset the timer
                
                # Draw a green border to indicate capture
                cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 20)
                cv2.imshow('Face Registration', frame)
                cv2.waitKey(100)  # Brief flash
                
                speak(f"Captured image {sample_count} of 20")
                
                # If we've captured all images, break out
                if sample_count >= 20:
                    # Make sure to release camera and close windows before processing
                    print("All 20 images captured. Closing camera and processing...")
                    cv2.destroyAllWindows()
                    cap.release()
                    
                    # Add a small delay to ensure windows are closed
                    time.sleep(0.5)
                    
                    # Make sure all OpenCV windows are really closed
                    for i in range(5):
                        cv2.waitKey(1)
                        
                    break
            
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                speak("Registration cancelled.")
                cap.release()
                cv2.destroyAllWindows()
                return False
        
        # Update the face recognition model
        try:
            print("Processing captured images and updating model...")
            # We need at least one sample to train the model
            if not face_samples:
                speak("No face samples were captured. Registration failed.")
                return False
                
            # Prepare training data
            ids = np.array([new_user_id] * len(face_samples))
            
            # Train the model or update if it already exists
            if hasattr(self.face_recognizer, 'update'):
                print("Updating existing model...")
                self.face_recognizer.update(face_samples, ids)
            else:
                print("Training new model...")
                self.face_recognizer.train(face_samples, ids)
            
            # Update labels
            self.labels[new_user_id] = user_name
            
            # Save the updated model
            print("Saving model to disk...")
            self.save_model()
            
            speak(f"Thank you {user_name}. Your face data has been registered successfully.")
            print(f"User {user_name} registered successfully with ID {new_user_id}")
            return True
            
        except Exception as e:
            speak("An error occurred during registration.")
            print(f"Registration error: {e}")
            return False
    
    def start_recognition(self):
        """Start face recognition in a separate thread"""
        if self.is_running:
            print("Face recognition is already running")
            return
            
        # Check if we have any models to work with
        if not hasattr(self, 'labels') or not self.labels:
            speak("No users are registered for facial recognition. Let's add a new user.")
            self.add_new_user()
            return
        
        self.is_running = True
        self.recognized_users.clear()
        self.recognition_thread = threading.Thread(target=self._recognition_worker)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
    
    def stop_recognition(self):
        """Stop face recognition"""
        self.is_running = False
        if self.recognition_thread:
            # Give the thread some time to clean up
            time.sleep(1)
            self.recognition_thread = None
    
    def _recognition_worker(self):
        """Worker function for continuous face recognition"""
        # Try different camera indices and backends
        camera_opened = False
        cap = None
        
        # Try different camera indices (0, 1, 2)
        for camera_index in range(3):
            try:
                # Try DirectShow backend first (more reliable on Windows)
                if hasattr(cv2, 'CAP_DSHOW'):
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        ret, test_frame = cap.read()
                        if ret:
                            camera_opened = True
                            print(f"Camera opened successfully with index {camera_index} using DirectShow")
                            break
                
                # Try with default backend
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret:
                        camera_opened = True
                        print(f"Camera opened successfully with index {camera_index} using default backend")
                        break
                    else:
                        print("Camera opened but couldn't read frames")
                        cap.release()
            except Exception as e:
                print(f"Error with camera index {camera_index}: {e}")
        
        if not camera_opened:
            print("Could not access any camera. Recognition failed.")
            speak("I'm having trouble accessing the camera. Please check your camera connection and privacy settings.")
            self.is_running = False
            return
        
        print("Starting facial recognition...")
        recognition_start_time = time.time()
        recognition_timeout = 15  # Run recognition for 15 seconds
        
        while self.is_running and (time.time() - recognition_start_time < recognition_timeout):
            ret, frame = cap.read()
            if not ret:
                continue
                
            gray, faces = self.detect_faces(frame)
            
            # For each detected face, try to recognize it
            for (x, y, w, h) in faces:
                # Draw a rectangle around the face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Recognize the face
                face_sample = gray[y:y+h, x:x+w]
                try:
                    user_id, confidence = self.face_recognizer.predict(face_sample)
                    
                    # Lower confidence means better match in OpenCV's LBPH
                    if confidence < 100:  # Adjust this threshold as needed
                        user_name = self.labels.get(user_id, "Unknown")
                        confidence_text = f"{round(100 - confidence)}%"
                        
                        # Display name and confidence
                        cv2.putText(frame, user_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.putText(frame, confidence_text, (x+w-70, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Greet the user if they haven't been greeted yet
                        if user_id not in self.recognized_users:
                            self.recognized_users.add(user_id)
                            speak(f"Hello {user_name}! Welcome back.")
                    else:
                        # Unknown face
                        cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                except Exception as e:
                    print(f"Error during face recognition: {e}")
            
            # Display the frame
            cv2.imshow('Face Recognition', frame)
            
            # Break the loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # If we didn't recognize anyone but found faces, offer to register them
        if not self.recognized_users and len(faces) > 0:
            speak("I noticed your face but didn't recognize you. Would you like to register as a new user?")
            # For demo purposes, let's simulate a 'yes' response
            # In a real implementation, use voice recognition
            print("Enter yes or no: ", end="")
            response = input().strip().lower()
            if response == "yes":
                self.add_new_user()
        elif not faces:
            print("No faces were detected during recognition")
        
        # Release camera and close windows
        print("Closing facial recognition session...")
        cap.release()
        cv2.destroyAllWindows()
        
        # Make sure all OpenCV windows are really closed
        for i in range(5):
            cv2.waitKey(1)
            
        self.is_running = False
    
    def list_users(self):
        """List all registered users"""
        # Check if labels attribute exists
        if not hasattr(self, 'labels'):
            self.labels = {}
            
        if not self.labels:
            speak("There are no registered users.")
            return []
        
        users = list(self.labels.values())
        speak(f"There are {len(users)} registered users: {', '.join(users)}")
        return users
    
    def remove_user(self, user_name):
        """Remove a user from the recognition model"""
        # Check if labels attribute exists
        if not hasattr(self, 'labels'):
            self.labels = {}
            speak("There are no registered users to remove.")
            return False
            
        # Find the user ID for the given name
        user_id = None
        for uid, name in self.labels.items():
            if name.lower() == user_name.lower():
                user_id = uid
                break
        
        if user_id is None:
            speak(f"User {user_name} not found.")
            return False
        
        # Remove the user from labels
        del self.labels[user_id]
        
        # We need to retrain the model completely to remove a user
        # This would require keeping the original training data, which is complex
        # For simplicity, we'll just update the labels file
        self.save_model()
        
        speak(f"User {user_name} has been removed.")
        return True