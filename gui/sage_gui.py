import tkinter as tk
from tkinter import scrolledtext, font, Canvas, Toplevel, Entry, Label, Button
import threading
import time
import sys
import os
import math
import io

# Create a global reference to the GUI instance that can be imported elsewhere
gui_instance = None

# Fix imports by adding parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import SAGE components
from assistant.text_to_speech import speak, stop_speaking, speaking, speech_lock
from assistant.voice_recognition import listen
from assistant.commands import Commands
from assistant.core import Assistant

# Custom input dialog that will work reliably
class InputDialog(Toplevel):
    def __init__(self, parent, title="Input Required", prompt="Please enter your response:"):
        super().__init__(parent)
        self.transient(parent)  # Set to be on top of the main window
        self.title(title)
        self.parent = parent
        self.result = None
        
        # Window setup
        self.geometry("400x150")
        self.resizable(False, False)
        self.configure(bg="#1E1E1E")
        
        # Dialog elements
        Label(self, text=prompt, font=("Segoe UI", 11), bg="#1E1E1E", fg="#E0E0E0", pady=10).pack(fill=tk.X)
        
        # Entry field
        self.entry = Entry(self, font=("Segoe UI", 11), bg="#333333", fg="#E0E0E0", insertbackground="#FFFFFF")
        self.entry.pack(fill=tk.X, padx=20, pady=5)
        self.entry.focus_set()
        
        # Button frame
        button_frame = tk.Frame(self, bg="#1E1E1E")
        button_frame.pack(pady=10)
        
        # OK and Cancel buttons
        Button(button_frame, text="OK", font=("Segoe UI", 10), bg="#00BFFF", fg="#1E1E1E", 
               command=self.on_ok, width=10).pack(side=tk.LEFT, padx=10)
               
        Button(button_frame, text="Cancel", font=("Segoe UI", 10), bg="#666666", fg="#E0E0E0",
               command=self.on_cancel, width=10).pack(side=tk.LEFT, padx=10)
        
        # Handle enter and escape keys
        self.bind("<Return>", lambda event: self.on_ok())
        self.bind("<Escape>", lambda event: self.on_cancel())
        
        # Make modal
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_window(self)
    
    def on_ok(self):
        """Get the result and close"""
        self.result = self.entry.get()
        self.destroy()
    
    def on_cancel(self):
        """Cancel and close"""
        self.result = None
        self.destroy()

# Redirect stdin to handle terminal input replacement
class InputRedirector:
    def __init__(self, gui):
        self.gui = gui
        self.buffer = ""
        
    def readline(self):
        # This replaces standard input with GUI input
        prompt = "Please enter your response:"
        
        # Look for specific prompts in recent messages
        if hasattr(self.gui, 'message_display'):
            content = self.gui.get_recent_messages()
            
            if "What's your name" in content or "what is your name" in content:
                prompt = "What's your name?"
            elif "email" in content.lower() and "address" in content.lower():
                prompt = "Please enter the email address:"
            elif "password" in content.lower():
                prompt = "Please enter the password:"
        
        # Use the GUI to get input
        result = self.gui.get_gui_input(prompt)
        if result:
            return result + '\n'  # Add newline for readline compatibility
        return '\n'  # Return empty line if canceled

class CircularVisualizer:
    """Class to create and update a circular audio visualization"""
    def __init__(self, canvas, center_x, center_y, radius, color="#00BFFF"):
        self.canvas = canvas
        self.center_x = center_x
        self.center_y = center_y
        self.base_radius = radius
        self.color = color
        self.is_active = False
        self.animation_id = None
        self.circle = None
        self.create_circle()
        
    def create_circle(self):
        """Create the initial circle"""
        self.circle = self.canvas.create_oval(
            self.center_x - self.base_radius, 
            self.center_y - self.base_radius,
            self.center_x + self.base_radius, 
            self.center_y + self.base_radius,
            outline=self.color, width=2, fill=""
        )
    
    def start(self):
        """Start the circular visualization animation"""
        self.is_active = True
        self.animate()
        
    def stop(self):
        """Stop the circular visualization animation"""
        self.is_active = False
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None
        # Reset to a perfect circle
        self.canvas.coords(
            self.circle,
            self.center_x - self.base_radius, 
            self.center_y - self.base_radius,
            self.center_x + self.base_radius, 
            self.center_y + self.base_radius
        )
    
    def animate(self):
        """Animate the circular visualization"""
        if not self.is_active:
            return
            
        # Generate a slightly deformed circle
        phase = time.time() * 2  # Animation speed
        
        # Calculate new radius with slight variations
        new_radius = self.base_radius * (1 + 0.05 * math.sin(phase))
        
        # Update the circle
        self.canvas.coords(
            self.circle,
            self.center_x - new_radius, 
            self.center_y - new_radius,
            self.center_x + new_radius, 
            self.center_y + new_radius
        )
        
        # Schedule the next animation frame
        self.animation_id = self.canvas.after(50, self.animate)

class SAGEGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Project S.A.G.E")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Add flag to track when we're waiting for a response to a specific prompt
        self.waiting_for_response = False
        
        # Set dark theme colors
        self.bg_color = "#121212"
        self.accent_color = "#00BFFF"
        self.text_color = "#E0E0E0"
        self.input_bg = "#1E1E1E"
        self.message_bg = "#1A1A1A"
        
        # Configure the root window
        self.root.configure(bg=self.bg_color)
        
        # Configure the grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)  # Visualization area
        self.root.grid_rowconfigure(1, weight=1)  # Message area
        self.root.grid_rowconfigure(2, weight=0)  # Input area
        
        # Create visualization area
        self.create_visualization_area()
        
        # Create the message area
        self.create_message_area()
        
        # Create the input area
        self.create_input_area()
        
        # Redirect standard input to our custom handler
        self.original_stdin = sys.stdin
        sys.stdin = InputRedirector(self)
        
        # Redirect standard output to capture SAGE output
        self.original_stdout = sys.stdout
        self.stdout_buffer = io.StringIO()
        sys.stdout = self.StdoutRedirector(self)
        
        # Replace the standard speak function with our GUI version
        self.original_speak = speak
        
        # Create a wrapper around speak that also updates the GUI
        def gui_speak(text):
            # Display in GUI
            self.display_assistant_message(text)
            # Call the original speak function
            self.original_speak(text)
            
        # Replace the speak function
        import assistant.text_to_speech
        assistant.text_to_speech.speak = gui_speak
        
        # Start visualization
        self.circular_vis.start()
        
        # State variables
        self.running = True
        self.continuous_listening = True
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize the assistant
        # We create a separate thread for this as it may take some time
        self.assistant = None
        self.commands = None
        threading.Thread(target=self.initialize_assistant, daemon=True).start()
        
        # Display welcome message
        self.display_system_message("Initializing SAGE Assistant...")

    class StdoutRedirector:
        def __init__(self, gui):
            self.gui = gui
            self.terminal = sys.stdout
            
        def write(self, message):
            # Write to the original stdout (terminal)
            self.terminal.write(message)
            
            # Look for terminal input prompts
            if "Enter your name:" in message or "Enter recipient's email address:" in message:
                # These are prompts that should trigger our GUI input
                # The stdin redirector will handle the actual input via readline
                pass
                
            # Filter out common debugging messages
            if not any(msg in message for msg in ["Revert to STA COM", "Detected camera", "Error with camera"]):
                # Display important messages in GUI
                if "[Assistant]:" in message:
                    # This is a message from the assistant (via speak function)
                    clean_msg = message.replace("[Assistant]:", "").strip()
                    if clean_msg:
                        self.gui.root.after(0, lambda: self.gui.display_assistant_message(clean_msg))
                elif "Error:" in message or "Exception:" in message:
                    # This is an error message
                    self.gui.root.after(0, lambda: self.gui.display_error_message(message.strip()))
            
        def flush(self):
            # This is needed for compatibility with sys.stdout
            pass
    
    def initialize_assistant(self):
        """Initialize the assistant in a background thread"""
        try:
            # Create the assistant (using the core module)
            self.assistant = Assistant()
            
            # Get the commands instance from the assistant
            self.commands = self.assistant.commands
            
            # Monkey-patch the get_response method in Commands class to set/reset waiting flag
            original_get_response = self.commands.get_response
            
            def patched_get_response(*args, **kwargs):
                # Set the waiting flag before getting a response
                self.waiting_for_response = True
                try:
                    # Call the original method
                    result = original_get_response(*args, **kwargs)
                    return result
                finally:
                    # Reset the waiting flag when done, even if there was an error
                    self.waiting_for_response = False
            
            # Replace the method
            self.commands.get_response = patched_get_response
            
            # Update GUI when done
            self.root.after(0, lambda: self.display_system_message("SAGE Assistant initialized successfully."))
            self.root.after(0, lambda: self.status_label.configure(text="SAGE Assistant - Always Listening"))
            
            # Display welcome messages
            self.root.after(0, lambda: self.display_assistant_message("Welcome to Project S.A.G.E! I'm your AI assistant."))
            self.root.after(0, lambda: self.display_assistant_message("I'm always listening for your commands."))
            
            # Start continuous listening
            self.root.after(0, self.start_continuous_listening)
            
            # Run facial recognition at startup to greet the user
            self.root.after(1000, self.startup_face_recognition)
            
        except Exception as e:
            # Update GUI with error
            error_msg = f"Error initializing SAGE: {str(e)}"
            self.root.after(0, lambda: self.display_error_message(error_msg))
            self.root.after(0, lambda: self.status_label.configure(text="Initialization Error"))
    
    def startup_face_recognition(self):
        """Run facial recognition at startup to greet the user"""
        if self.assistant and hasattr(self.assistant, 'startup_face_recognition'):
            threading.Thread(target=self.assistant.startup_face_recognition, daemon=True).start()
        
    def create_visualization_area(self):
        """Create the visualization area at the top of the window"""
        vis_frame = tk.Frame(self.root, bg=self.bg_color, height=150)
        vis_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Create a canvas for the visualization
        self.vis_canvas = tk.Canvas(
            vis_frame, 
            width=780, 
            height=120, 
            bg=self.bg_color, 
            highlightthickness=0
        )
        self.vis_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add the circular visualizer in the center
        canvas_width = 780
        canvas_height = 120
        self.circular_vis = CircularVisualizer(
            self.vis_canvas, 
            canvas_width//2, 
            canvas_height//2, 
            50, 
            color=self.accent_color
        )
        
        # Add a label for the assistant status
        self.status_label = tk.Label(
            vis_frame,
            text="Initializing...",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.accent_color
        )
        self.status_label.pack(pady=(0, 5))
        
    def create_message_area(self):
        """Create the scrollable message area where conversation is displayed"""
        # Create a frame for the message display
        message_frame = tk.Frame(self.root, bg=self.bg_color)
        message_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame.grid_rowconfigure(0, weight=1)
        
        # Create the message display
        self.message_display = scrolledtext.ScrolledText(
            message_frame,
            wrap=tk.WORD,
            bg=self.message_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.accent_color,
            selectforeground=self.text_color,
            font=("Segoe UI", 11),
            padx=15,
            pady=15,
            borderwidth=0
        )
        self.message_display.grid(row=0, column=0, sticky="nsew")
        self.message_display.configure(state=tk.DISABLED)
        
        # Create custom tags for different message types
        self.message_display.tag_configure(
            "user", 
            foreground="#96D0FF",  # Light blue for user
            font=("Segoe UI", 11)
        )
        self.message_display.tag_configure(
            "assistant", 
            foreground="#28B463",  # Green for assistant
            font=("Segoe UI", 11, "bold")
        )
        self.message_display.tag_configure(
            "system", 
            foreground="#F5B041",  # Orange for system
            font=("Segoe UI", 11)
        )
        self.message_display.tag_configure(
            "error", 
            foreground="#E74C3C",  # Red for errors
            font=("Segoe UI", 11)
        )
        
    def create_input_area(self):
        """Create the input area at the bottom of the window"""
        input_frame = tk.Frame(self.root, bg=self.input_bg, padx=0, pady=0)
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Create a style for rounded elements
        rounded_frame = tk.Frame(
            input_frame, 
            bg=self.input_bg, 
            bd=1, 
            relief=tk.SOLID,
            highlightbackground=self.accent_color,
            highlightthickness=1
        )
        rounded_frame.grid(row=0, column=0, sticky="ew", columnspan=3, padx=0, pady=0)
        rounded_frame.grid_columnconfigure(0, weight=1)
        
        # Create the input field
        self.input_field = tk.Entry(
            rounded_frame,
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("Segoe UI", 11),
            bd=0,
            highlightthickness=0
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        self.input_field.bind("<Return>", lambda event: self.submit_input())
        
        # Create a microphone indicator (always on)
        mic_frame = tk.Frame(rounded_frame, bg=self.input_bg)
        mic_frame.grid(row=0, column=1, padx=5, pady=5)
        
        self.mic_button = tk.Label(
            mic_frame,
            text="🎤",
            font=("Segoe UI", 12),
            bg=self.input_bg,
            fg=self.accent_color,
            padx=10
        )
        self.mic_button.pack(fill=tk.BOTH, expand=True)
        
        # Create a send button
        send_frame = tk.Frame(rounded_frame, bg=self.input_bg)
        send_frame.grid(row=0, column=2, padx=5, pady=5)
        
        self.send_button = tk.Button(
            send_frame,
            text="Send",
            font=("Segoe UI", 10),
            bg=self.input_bg,
            fg=self.accent_color,
            activebackground=self.accent_color,
            activeforeground=self.input_bg,
            bd=0,
            padx=10,
            command=self.submit_input
        )
        self.send_button.pack(fill=tk.BOTH, expand=True)
    
    def get_gui_input(self, prompt):
        """Get input from the user using a GUI dialog"""
        # Set the waiting flag to prevent continuous listening from capturing this input
        was_waiting = self.waiting_for_response
        self.waiting_for_response = True
        
        try:
            dialog = InputDialog(self.root, "SAGE Assistant", prompt)
            if dialog.result:
                # Show the user's input in the chat
                self.display_user_message(dialog.result)
            return dialog.result
        finally:
            # Restore the waiting flag to its previous state
            self.waiting_for_response = was_waiting
        
    def get_recent_messages(self):
        """Get the most recent messages from the chat window"""
        # Return the last 1000 characters of the message display
        self.message_display.configure(state=tk.NORMAL)
        end_index = self.message_display.index(tk.END)
        start_index = f"{float(end_index) - 1000.0}"
        recent_text = self.message_display.get(start_index, end_index)
        self.message_display.configure(state=tk.DISABLED)
        return recent_text
        
    def start_continuous_listening(self):
        """Start a continuous listening thread that always listens for commands"""
        def continuous_listen():
            # This flag controls whether we're in normal mode or just waiting for "wake up"
            waiting_for_wakeup = False
            
            # Track the last processed command to avoid duplicates
            last_command = ""
            last_command_time = 0
            
            while self.continuous_listening and self.running:
                try:
                    # If we're waiting for a response to a specific function prompt,
                    # don't process new commands until that's done
                    if self.waiting_for_response:
                        time.sleep(0.5)  # Short sleep to avoid CPU hogging
                        continue
                    
                    # If any speech is still happening, wait for it to finish
                    if speaking:
                        time.sleep(0.2)
                        continue
                        
                    # Subtle indication that we're actively listening
                    self.root.after(0, lambda: self.mic_button.configure(fg="#FF6B6B"))  # Brief color change
                    
                    # Listen for command
                    command = listen(timeout=5)  # Use a shorter timeout
                    
                    # Reset mic color
                    if waiting_for_wakeup:
                        # Keep the microphone gray in muted state
                        self.root.after(0, lambda: self.mic_button.configure(fg="#888888"))
                    else:
                        # Normal active color
                        self.root.after(0, lambda: self.mic_button.configure(fg=self.accent_color))
                    
                    # Check if we got a valid command and it's not a duplicate
                    if command and len(command.strip()) > 0:
                        current_time = time.time()
                        
                        # Prevent duplicate/rapid processing of the same command
                        # (must be different command or at least 2 seconds since last time)
                        if (command != last_command or 
                                current_time - last_command_time > 2.0):
                            
                            # Update last command tracking
                            last_command = command
                            last_command_time = current_time
                            
                            # Display the command
                            self.display_user_message(command)
                            
                            # If we're waiting for wake up, only process that command
                            if waiting_for_wakeup:
                                if "wake up" in command.lower():
                                    waiting_for_wakeup = False
                                    self.resume_assistant()
                                # Ignore all other commands while muted
                            else:
                                # Check for mute command first
                                if "mute" in command.lower():
                                    waiting_for_wakeup = True
                                    self.pause_assistant()
                                else:
                                    # Update indicator to show we heard something
                                    self.root.after(0, lambda: self.status_label.configure(text="Command received..."))
                                    
                                    # Process the command in a separate thread
                                    process_thread = threading.Thread(
                                        target=self.process_command, 
                                        args=(command,), 
                                        daemon=True
                                    )
                                    process_thread.start()
                                    
                                    # Wait for processing to finish before listening again
                                    # This helps prevent overlapping commands
                                    process_thread.join(timeout=0.5)
                except Exception as e:
                    print(f"Error in continuous listening: {e}")
                    # Brief pause to avoid hogging CPU on errors
                    time.sleep(1)
            
            print("Continuous listening thread stopped")
        
        # Start the listening thread
        listening_thread = threading.Thread(target=continuous_listen, daemon=True)
        listening_thread.start()
        
    def submit_input(self):
        """Handle submission from the input field"""
        text = self.input_field.get().strip()
        if not text:
            return
            
        # Display the user's input
        self.display_user_message(text)
        
        # Clear the input field
        self.input_field.delete(0, tk.END)
        
        # Process as a normal command
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()
        

    # This is a partial fix for sage_gui.py
    # Focus on the continuous_listen function in the SAGEGui class

    def continuous_listen(self):
        """Start a continuous listening thread that always listens for commands"""
        # This flag controls whether we're in normal mode or just waiting for "wake up"
        waiting_for_wakeup = False
        
        # Track the last processed command to avoid duplicates
        last_command = ""
        last_command_time = 0
        
        while self.continuous_listening and self.running:
            try:
                # If we're waiting for a response to a specific function prompt,
                # don't process new commands until that's done
                if self.waiting_for_response:
                    time.sleep(0.5)  # Short sleep to avoid CPU hogging
                    continue
                
                # If any speech is still happening, wait for it to finish
                if speaking:
                    time.sleep(0.2)
                    continue
                    
                # Check if the assistant is processing a command or waiting for conversation input
                if hasattr(self.assistant, 'processing_command') and self.assistant.processing_command:
                    time.sleep(0.2)  # Wait for the current command to finish
                    continue
                    
                if hasattr(self.commands, 'in_conversation') and self.commands.in_conversation:
                    time.sleep(0.2)  # Wait for the conversation to finish
                    continue
                    
                # Subtle indication that we're actively listening
                self.root.after(0, lambda: self.mic_button.configure(fg="#FF6B6B"))  # Brief color change
                
                # Listen for command
                command = listen(timeout=5)  # Use a shorter timeout
                
                # Reset mic color
                if waiting_for_wakeup:
                    # Keep the microphone gray in muted state
                    self.root.after(0, lambda: self.mic_button.configure(fg="#888888"))
                else:
                    # Normal active color
                    self.root.after(0, lambda: self.mic_button.configure(fg=self.accent_color))
                
                # Check if we got a valid command and it's not a duplicate
                if command and len(command.strip()) > 0:
                    current_time = time.time()
                    
                    # Prevent duplicate/rapid processing of the same command
                    # (must be different command or at least 2 seconds since last time)
                    if (command != last_command or 
                            current_time - last_command_time > 2.0):
                        
                        # Update last command tracking
                        last_command = command
                        last_command_time = current_time
                        
                        # Display the command
                        self.display_user_message(command)
                        
                        # If we're waiting for wake up, only process that command
                        if waiting_for_wakeup:
                            if "wake up" in command.lower():
                                waiting_for_wakeup = False
                                self.resume_assistant()
                            # Ignore all other commands while muted
                        else:
                            # Check for mute command first
                            if "mute" in command.lower():
                                waiting_for_wakeup = True
                                self.pause_assistant()
                            else:
                                # Update indicator to show we heard something
                                self.root.after(0, lambda: self.status_label.configure(text="Command received..."))
                                
                                # Process the command in a separate thread
                                process_thread = threading.Thread(
                                    target=self.process_command, 
                                    args=(command,), 
                                    daemon=True
                                )
                                process_thread.start()
                                
                                # Wait for processing to start but don't block
                                # This helps prevent overlapping commands
                                time.sleep(0.5)
            except Exception as e:
                print(f"Error in continuous listening: {e}")
                # Brief pause to avoid hogging CPU on errors
                time.sleep(1)
        
        print("Continuous listening thread stopped")

    # Updated process_command function for SAGEGui
    def process_command(self, command):
        """Process the user's command"""
        if not self.commands:
            self.display_system_message("SAGE is still initializing. Please wait...")
            return
            
        try:
            # Update status and set assistant's processing flag
            if hasattr(self.assistant, 'processing_command'):
                self.assistant.processing_command = True
                
            self.root.after(0, lambda: self.status_label.configure(text="Processing..."))
            
            # Handle built-in commands
            if command.lower() in ["exit", "quit", "end assistant"]:
                self.display_assistant_message("Shutting down. Goodbye!")
                self.root.after(2000, self.on_closing)
                return
            
            # Special handling for visualization
            if "visualize" in command.lower() or "activate" in command.lower():
                self.circular_vis.start()
                self.display_assistant_message("Visualization activated!")
                self.root.after(0, lambda: self.status_label.configure(text="SAGE Assistant - Always Listening"))
                if hasattr(self.assistant, 'processing_command'):
                    self.assistant.processing_command = False
                return
                
            if "stop visualization" in command.lower() or "deactivate" in command.lower():
                self.circular_vis.stop()
                self.display_assistant_message("Visualization deactivated.")
                self.root.after(0, lambda: self.status_label.configure(text="SAGE Assistant - Always Listening"))
                if hasattr(self.assistant, 'processing_command'):
                    self.assistant.processing_command = False
                return
                
            # All other commands are handled by the Commands class
            self.commands.process_command(command)
            
            # Reset status when done
            self.root.after(0, lambda: self.status_label.configure(text="SAGE Assistant - Always Listening"))
            
            # Reset assistant's processing flag
            if hasattr(self.assistant, 'processing_command'):
                self.assistant.processing_command = False
                
        except Exception as e:
            self.root.after(0, lambda: self.status_label.configure(text="Error"))
            self.display_error_message(f"Error processing command: {e}")
            # Reset assistant's processing flag on error
            if hasattr(self.assistant, 'processing_command'):
                self.assistant.processing_command = False


    def pause_assistant(self):
        """Pause the assistant when 'mute' command is given"""
        self.display_assistant_message("Assistant paused. Say 'wake up' to resume.")
        self.root.after(0, lambda: self.status_label.configure(text="SAGE Assistant - Paused"))
        # Visual indication of paused state
        self.root.after(0, lambda: self.mic_button.configure(fg="#888888"))

    def resume_assistant(self):
        """Resume the assistant when 'wake up' command is given"""
        self.display_assistant_message("Assistant resumed and listening.")
        self.root.after(0, lambda: self.status_label.configure(text="SAGE Assistant - Always Listening"))
        # Visual indication of active state
        self.root.after(0, lambda: self.mic_button.configure(fg=self.accent_color))
            
    def display_user_message(self, message):
        """Display a message from the user"""
        self.message_display.configure(state=tk.NORMAL)
        if self.message_display.index('end-1c') != '1.0':
            self.message_display.insert(tk.END, '\n\n')
        self.message_display.insert(tk.END, "You: ", "user")
        self.message_display.insert(tk.END, message)
        self.message_display.see(tk.END)
        self.message_display.configure(state=tk.DISABLED)
        
    def display_assistant_message(self, message):
        """Display a message from the assistant"""
        self.message_display.configure(state=tk.NORMAL)
        if self.message_display.index('end-1c') != '1.0':
            self.message_display.insert(tk.END, '\n\n')
        self.message_display.insert(tk.END, "SAGE: ", "assistant")
        self.message_display.insert(tk.END, message)
        self.message_display.see(tk.END)
        self.message_display.configure(state=tk.DISABLED)
        
    def display_system_message(self, message):
        """Display a system message"""
        self.message_display.configure(state=tk.NORMAL)
        if self.message_display.index('end-1c') != '1.0':
            self.message_display.insert(tk.END, '\n\n')
        self.message_display.insert(tk.END, "System: ", "system")
        self.message_display.insert(tk.END, message)
        self.message_display.see(tk.END)
        self.message_display.configure(state=tk.DISABLED)
        
    def display_error_message(self, message):
        """Display an error message"""
        self.message_display.configure(state=tk.NORMAL)
        if self.message_display.index('end-1c') != '1.0':
            self.message_display.insert(tk.END, '\n\n')
        self.message_display.insert(tk.END, "Error: ", "error")
        self.message_display.insert(tk.END, message)
        self.message_display.see(tk.END)
        self.message_display.configure(state=tk.DISABLED)
        
    def on_closing(self):
        """Handle window closing event"""
        # Stop continuous listening
        self.continuous_listening = False
        
        # Stop any active visualizations
        self.circular_vis.stop()
        
        # Restore original stdin and stdout
        sys.stdin = self.original_stdin
        sys.stdout = self.original_stdout
        
        # Restore original speak function
        import assistant.text_to_speech
        assistant.text_to_speech.speak = self.original_speak
        
        # Set running flag to False
        self.running = False
        
        # Close the window
        self.root.destroy()
        
        # Exit the application
        sys.exit(0)

# Main function to run the GUI
def main():
    try:
        global gui_instance
        root = tk.Tk()
        app = SAGEGui(root)
        gui_instance = app  # Set the global reference
        root.mainloop()
    except Exception as e:
        print(f"Error running SAGE GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()