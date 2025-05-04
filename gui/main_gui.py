#!/usr/bin/env python3
# main_gui.py - Main entry point for SAGE Assistant GUI

import os
import sys
import traceback
import tkinter as tk
from tkinter import messagebox

# Add the parent directory to the Python path so we can import assistant modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "tkinter", "pyttsx3", "speech_recognition", 
        "requests", "numpy"
    ]
    
    optional_packages = ["opencv-python"]
    
    missing_packages = []
    missing_optional = []
    
    for package in required_packages:
        try:
            # Special case for tkinter which is part of standard library
            if package == "tkinter":
                import tkinter
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    for package in optional_packages:
        try:
            if package == "opencv-python":
                import cv2
            else:
                __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_optional:
        print(f"Warning: Some optional features may not work. Missing packages: {', '.join(missing_optional)}")
        print(f"To install optional packages: pip install {' '.join(missing_optional)}")
    
    return missing_packages

def main():
    """Main entry point for the SAGE Assistant GUI"""
    try:
        # Check dependencies first
        missing_packages = check_dependencies()
        if missing_packages:
            packages_str = ", ".join(missing_packages)
            print(f"Warning: Missing required packages: {packages_str}")
            print("You can install them using pip:")
            print(f"pip install {' '.join(missing_packages)}")
            
            # Show a graphical error if tkinter is available
            try:
                # Note: We already imported tk at the top of the file
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                messagebox.showerror(
                    "Missing Dependencies",
                    f"The following required packages are missing:\n\n{packages_str}\n\n" +
                    f"Please install them using pip:\npip install {' '.join(missing_packages)}"
                )
                
                root.destroy()
            except:
                # If tkinter isn't available, we already printed the error
                pass
                
            return
        
        # Import the GUI after confirming dependencies
        from sage_gui import SAGEGui
        
        # Create and run the GUI
        root = tk.Tk()
        app = SAGEGui(root)
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Error starting SAGE Assistant: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        # Show a graphical error if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("SAGE Assistant Error", error_msg)
            root.destroy()
        except:
            # If tkinter isn't available, we already printed the error
            pass

if __name__ == "__main__":
    main()