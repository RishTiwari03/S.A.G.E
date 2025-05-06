# core.py

from assistant.commands import Commands
from assistant.text_to_speech import speak, stop_speaking, speaking, speech_lock
from assistant.voice_recognition import listen
import sys
import time
import threading

# Define the variable at the module level
facial_recognition_available = False

# Try to import facial recognition, but don't fail if it's not available
try:
    from assistant.facial_recognition import FacialRecognizer
    facial_recognition_available = True
    print("Facial recognition module imported successfully")
except Exception as e:
    print(f"Facial recognition could not be loaded: {e}")
    facial_recognition_available = False

class Assistant:
    def __init__(self):
        self.commands = Commands()
        self.paused = False
        self.running = True
        self.face_recognizer = None
        
        # Add a flag to control command processing
        self.processing_command = False
        
        # Initialize text-to-speech (this is now handled by the module itself)
        print("Text-to-speech system initialized.")
        
        # Only initialize facial recognition if it's available
        global facial_recognition_available
        
        if facial_recognition_available:
            try:
                self.face_recognizer = FacialRecognizer()
                print("Facial recognition initialized.")
            except Exception as e:
                print(f"Error initializing facial recognition: {e}")
                # If there's an error, make sure this is set to False
                facial_recognition_available = False
        
    def run(self):
        print("SAGE is now listening...")
        speak("SAGE assistant is ready")
        
        # Give time for speech to complete
        time.sleep(1)
        
        # Start facial recognition only if it's available
        if facial_recognition_available and self.face_recognizer is not None:
            try:
                # Check if a camera is actually available
                camera_available = self.face_recognizer.is_camera_available()
                if camera_available:
                    threading.Thread(target=self.startup_face_recognition, daemon=True).start()
                    print("Facial recognition started in background thread")
                else:
                    print("No camera detected. Facial recognition disabled.")
                    speak("I don't detect a camera on your system. Facial recognition features are disabled.")
                    time.sleep(1)  # Wait for speech to complete
            except Exception as e:
                print(f"Could not start facial recognition: {e}")
                print("Continuing without facial recognition")
        else:
            print("Facial recognition is not available. Running without it.")
        
        # Add a small delay to ensure the first speak command completes
        time.sleep(1)
        
        while self.running:
            try:
                # Check if the assistant is in a paused state
                if self.paused:
                    self.wait_for_start_command()
                    continue

                # Check if a command is being processed or a response is expected
                if self.processing_command or self.commands.waiting_for_response or self.commands.in_conversation:
                    # Skip listening until the current command processing is complete
                    time.sleep(0.2)
                    continue

                # Listen to the user command
                command = listen()
                if command:
                    if "mute" in command:
                        self.pause()
                    elif "end assistant" in command:
                        self.stop()
                    else:
                        try:
                            # Set the flag to indicate a command is being processed
                            self.processing_command = True
                            
                            # Process the command
                            self.commands.process_command(command)
                            
                            # Reset the flag when done
                            self.processing_command = False
                        except Exception as e:
                            print(f"Error processing command: {e}")
                            # Stop any ongoing speech to prevent overlap
                            stop_speaking()
                            # Wait briefly before speaking again
                            time.sleep(0.5)
                            speak("I encountered an error processing that command.")
                            self.processing_command = False
            except Exception as e:
                print(f"Error in main loop: {e}")
                # If we encounter any error, stop speaking and reset
                stop_speaking()
                self.processing_command = False
                time.sleep(1)

    def startup_face_recognition(self):
        """Runs facial recognition at startup to greet users"""
        if not facial_recognition_available or self.face_recognizer is None:
            return
            
        try:
            # Start face recognition
            self.face_recognizer.start_recognition()
            
            # Recognition will continue in its own thread and greet recognized users
            # or offer to register new users
        except Exception as e:
            print(f"Error during facial recognition: {e}")

    def pause(self):
        """Pauses the assistant when the user says 'mute'."""
        self.paused = True
        speak("Assistant paused.")

    def stop(self):
        """Stops the assistant and exits the program when the user says 'end assistant'."""
        speak("Shutting down. Goodbye!")
        print("Assistant terminated.")
        self.running = False
        # Stop facial recognition if it's running
        if facial_recognition_available and self.face_recognizer is not None:
            try:
                self.face_recognizer.stop_recognition()
            except:
                pass
                
        # Allow time for final message to be spoken
        time.sleep(2)
        
        sys.exit(0)

    def wait_for_start_command(self):
        """Waits for the user to say 'wake up' to resume from a paused state."""
        while self.paused:
            command = listen()
            if command and "wake up" in command:
                self.paused = False
                speak("Resuming.")
                break
            elif command and "end assistant" in command:
                self.stop()