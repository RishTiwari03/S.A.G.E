# test_camera_gui.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import cv2
import threading
import time
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import text-to-speech
try:
    from assistant.text_to_speech import speak
except ImportError:
    # Fallback speak function if module not available
    def speak(text):
        print(f"[SPEAK]: {text}")

class CameraTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SAGE Camera Test")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Set dark theme colors
        self.bg_color = "#121212"
        self.accent_color = "#00BFFF"
        self.text_color = "#E0E0E0"
        
        # Configure the root window
        self.root.configure(bg=self.bg_color)
        
        # Create UI elements
        self.create_ui()
        
        # Variables
        self.camera_running = False
        self.cap = None
        self.video_thread = None
        
    def create_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title label
        title_label = tk.Label(
            main_frame,
            text="SAGE Camera Test Utility",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        title_label.pack(pady=(0, 20))
        
        # Create frame for camera view
        self.video_frame = tk.Frame(
            main_frame,
            bg="#1E1E1E",
            width=640,
            height=480,
            highlightbackground=self.accent_color,
            highlightthickness=1
        )
        self.video_frame.pack(pady=10)
        self.video_frame.pack_propagate(False)  # Don't resize based on content
        
        # Put a label inside to display camera feed
        self.video_label = tk.Label(self.video_frame, bg="#1E1E1E")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Camera not started",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.status_label.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(pady=10)
        
        # Start camera button
        self.start_button = tk.Button(
            button_frame,
            text="Start Camera",
            font=("Segoe UI", 10),
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground="#0078D7",
            activeforeground=self.text_color,
            padx=20,
            pady=5,
            command=self.start_camera
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Stop camera button
        self.stop_button = tk.Button(
            button_frame,
            text="Stop Camera",
            font=("Segoe UI", 10),
            bg="#666666",
            fg=self.text_color,
            activebackground="#888888",
            activeforeground=self.text_color,
            padx=20,
            pady=5,
            command=self.stop_camera,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Test facial recognition button
        self.face_button = tk.Button(
            button_frame,
            text="Test Face Detection",
            font=("Segoe UI", 10),
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground="#0078D7",
            activeforeground=self.text_color,
            padx=20,
            pady=5,
            command=self.test_face_detection,
            state=tk.DISABLED
        )
        self.face_button.pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = tk.Frame(main_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Log label
        log_label = tk.Label(
            log_frame,
            text="Camera Log",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        log_label.pack(anchor=tk.W)
        
        # Log text
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            bg="#1E1E1E",
            fg=self.text_color,
            font=("Consolas", 10),
            padx=10,
            pady=10,
            height=6
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("[%H:%M:%S]")
        log_message = f"{timestamp} {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_camera(self):
        """Start camera capture"""
        if self.camera_running:
            return
            
        self.log("Starting camera...")
        self.status_label.config(text="Starting camera...")
        
        # Try to open camera in a thread
        threading.Thread(target=self._start_camera_thread, daemon=True).start()
        
    def _start_camera_thread(self):
        """Thread for opening camera to avoid blocking UI"""
        try:
            # Try different camera indices and APIs
            apis = [cv2.CAP_ANY]
            
            # Add platform-specific APIs
            import platform
            if platform.system() == "Windows":
                apis = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            elif platform.system() == "Darwin":  # macOS
                apis = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
            else:  # Linux
                apis = [cv2.CAP_V4L2, cv2.CAP_ANY]
                
            for camera_index in range(3):  # Try indices 0, 1, 2
                for api in apis:
                    self.root.after(0, lambda: self.log(f"Trying camera index {camera_index} with API {api}..."))
                    try:
                        if api == cv2.CAP_ANY:
                            self.cap = cv2.VideoCapture(camera_index)
                        else:
                            self.cap = cv2.VideoCapture(camera_index, api)
                            
                        if self.cap.isOpened():
                            # Try to read a frame
                            ret, frame = self.cap.read()
                            if ret:
                                self.root.after(0, lambda: self.log(f"Successfully opened camera index {camera_index}"))
                                self.camera_running = True
                                
                                # Update UI from main thread
                                self.root.after(0, self._update_camera_ui)
                                
                                # Start video thread
                                self.video_thread = threading.Thread(target=self._update_video, daemon=True)
                                self.video_thread.start()
                                
                                return
                            else:
                                self.root.after(0, lambda: self.log("Could not read frame, trying next option"))
                                self.cap.release()
                    except Exception as e:
                        self.root.after(0, lambda: self.log(f"Error with camera {camera_index}, API {api}: {e}"))
            
            # If we get here, all camera options failed
            self.root.after(0, lambda: self.log("Failed to open any camera"))
            self.root.after(0, lambda: self.status_label.config(text="Camera not available"))
            messagebox.showerror("Camera Error", "Could not open any camera. Please check your camera connection.")
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error starting camera: {e}"))
            self.root.after(0, lambda: self.status_label.config(text="Error starting camera"))
            
    def _update_camera_ui(self):
        """Update UI after camera started successfully"""
        self.status_label.config(text="Camera running")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.face_button.config(state=tk.NORMAL)
        
    def _update_video(self):
        """Update video feed continuously"""
        while self.camera_running:
            try:
                if self.cap is not None and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # Convert OpenCV BGR format to RGB for tkinter
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Resize frame to fit video frame if needed
                        frame_height, frame_width = rgb_frame.shape[:2]
                        video_width = self.video_frame.winfo_width()
                        video_height = self.video_frame.winfo_height()
                        
                        # Calculate scaling factor to fit frame in video_frame
                        scale = min(video_width/frame_width, video_height/frame_height)
                        new_width = int(frame_width * scale)
                        new_height = int(frame_height * scale)
                        
                        # Resize frame
                        resized_frame = cv2.resize(rgb_frame, (new_width, new_height))
                        
                        # Convert to PhotoImage
                        from PIL import Image, ImageTk
                        img = Image.fromarray(resized_frame)
                        imgtk = ImageTk.PhotoImage(image=img)
                        
                        # Update label
                        self.video_label.imgtk = imgtk  # Keep reference to avoid garbage collection
                        self.video_label.config(image=imgtk)
                    else:
                        # Failed to read frame
                        self.root.after(0, lambda: self.log("Failed to read frame from camera"))
                        break
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error updating video: {e}"))
                break
                
            time.sleep(0.03)  # ~30 FPS
            
        # Clean up if loop exits
        self.camera_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
        # Reset UI in main thread
        self.root.after(0, lambda: self.status_label.config(text="Camera stopped"))
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.face_button.config(state=tk.DISABLED))
        
    def stop_camera(self):
        """Stop camera capture"""
        self.camera_running = False
        self.log("Stopping camera...")
        
        # Clear the video display
        self.video_label.config(image='')
        
    def test_face_detection(self):
        """Test face detection with current camera"""
        if not self.camera_running:
            messagebox.showinfo("Camera Required", "Please start the camera first.")
            return
            
        self.log("Testing face detection...")
        self.status_label.config(text="Face detection active")
        
        # Load face detector
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Capture a single frame
            ret, frame = self.cap.read()
            if not ret:
                self.log("Failed to capture frame for face detection")
                return
                
            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
            # Show result
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            from PIL import Image, ImageTk
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
            
            # Log results
            if len(faces) > 0:
                self.log(f"Detected {len(faces)} face(s)")
                speak(f"I detected {len(faces)} face or faces in the image.")
            else:
                self.log("No faces detected")
                speak("I don't see any faces. Please make sure your face is visible to the camera.")
                
        except Exception as e:
            self.log(f"Face detection error: {e}")
            messagebox.showerror("Face Detection Error", f"Error during face detection: {e}")
    
    def on_closing(self):
        """Handle window close event"""
        # Stop camera if running
        self.camera_running = False
        if self.cap is not None:
            self.cap.release()
            
        # Destroy window
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraTestApp(root)
    root.mainloop()