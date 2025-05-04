# text_to_speech.py

import pyttsx3
import time
import threading

# Variables that existing code might be importing
speaking = False
speech_lock = threading.Lock()  # Add a threading lock to coordinate speech access

# Try to initialize pyttsx3
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  
    engine.setProperty('volume', 1.0)
    print("Text-to-speech initialized with pyttsx3")
    
    # Try to get and list available voices
    voices = engine.getProperty('voices')
    print(f"Available voices: {len(voices)}")
    if len(voices) > 0:
        print(f"Setting voice to: {voices[0].name}")
        engine.setProperty('voice', voices[0].id)
except Exception as e:
    print(f"Error initializing pyttsx3: {e}")
    engine = None

# Try to initialize Windows SAPI (Windows only)
try:
    import win32com.client
    win_speaker = win32com.client.Dispatch("SAPI.SpVoice")
    win_speaker.Volume = 100  # 0 to 100
    win_speaker.Rate = 0      # -10 to 10 (0 is normal)
    print("Windows SAPI initialized")
except Exception as e:
    print(f"Error initializing Windows SAPI: {e}")
    win_speaker = None

def speak(text):
    """Speaking function with proper locking and status tracking."""
    global speaking, speech_lock
    
    # Always print what should be spoken
    print(f"[Assistant]: {text}")
    
    # Use a lock to ensure only one speech happens at a time
    with speech_lock:
        speaking = True
        speech_success = False
        
        # Try pyttsx3 first
        if engine is not None:
            try:
                engine.say(text)
                engine.runAndWait()
                speech_success = True
                print("Speech completed via pyttsx3")
            except Exception as e:
                print(f"pyttsx3 error: {e}")
        
        # If pyttsx3 failed, try Windows SAPI
        if not speech_success and win_speaker is not None:
            try:
                win_speaker.Speak(text)
                speech_success = True
                print("Speech completed via Windows SAPI")
            except Exception as e:
                print(f"Windows SAPI error: {e}")
        
        # If all methods failed, just print
        if not speech_success:
            print(f"All speech methods failed for: {text}")
        
        speaking = False
        return speech_success

def stop_speaking():
    """Stop any current speech."""
    global speaking, engine, win_speaker
    
    speaking = False
    
    # Try to stop pyttsx3
    if engine is not None:
        try:
            engine.stop()
        except:
            pass
    
    # Try to stop Windows SAPI
    if win_speaker is not None:
        try:
            win_speaker.Skip("Sentence")
        except:
            pass

# Test function
def test_speech():
    """Test if text-to-speech is working."""
    print("\n==== TESTING TEXT-TO-SPEECH ====")
    
    # Test basic speech
    print("Testing basic speech...")
    success = speak("This is a test of the speech system.")
    time.sleep(1)
    
    if success:
        speak("If you can hear this message, the text to speech is working correctly.")
        time.sleep(2)
        print("Speech test successful")
    else:
        print("Speech test failed - could not generate audio output")
    
    print("Test complete")

# Run test if this file is executed directly
if __name__ == "__main__":
    test_speech()