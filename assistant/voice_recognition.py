# voice_recognition.py

import speech_recognition as sr
import time
from assistant.text_to_speech import speaking, speech_lock

recognizer = sr.Recognizer()

def listen(timeout=10):
    # Wait until speaking is done before listening
    while speaking:
        time.sleep(0.2)
    
    # Now proceed with listening
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout)
            command = recognizer.recognize_google(audio)
            print(f"Recognized: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.WaitTimeoutError:
            print("Listening timed out")
            return None
        except Exception as e:
            print(f"Error in listen function: {e}")
            return None