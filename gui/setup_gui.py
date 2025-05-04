#!/usr/bin/env python3
# setup_gui.py - Script to set up the directory structure for the SAGE GUI

import os
import shutil
import sys

def setup_gui_structure():
    """
    Create the necessary directory structure for the SAGE GUI
    and copy files to their correct locations
    """
    print("Setting up Project SAGE GUI...")
    
    # The root directory is where this script is located
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define directories to create
    gui_dir = os.path.join(root_dir, "gui")
    
    # Create directories if they don't exist
    directories = [gui_dir]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    # Create the GUI icon file (placeholder)
    icon_path = os.path.join(gui_dir, "sage_icon.ico")
    if not os.path.exists(icon_path):
        try:
            # Create a simple text file as a placeholder
            with open(icon_path, 'w') as f:
                f.write("# This is a placeholder for the SAGE icon file\n")
                f.write("# Replace with an actual .ico file for a proper icon\n")
            print(f"Created placeholder icon file: {icon_path}")
            print("Note: For a proper icon, replace this with an actual .ico file")
        except Exception as e:
            print(f"Warning: Could not create icon placeholder: {e}")
    
    # Create __init__.py file in the gui directory to make it a package
    init_path = os.path.join(gui_dir, "__init__.py")
    if not os.path.exists(init_path):
        try:
            with open(init_path, 'w') as f:
                f.write("# GUI package for Project SAGE\n")
            print(f"Created file: {init_path}")
        except Exception as e:
            print(f"Warning: Could not create file {init_path}: {e}")
    
    # Check for files that need to be moved/copied
    files_to_check = [
        {"name": "sage_gui.py", "source": root_dir, "dest": gui_dir},
        {"name": "main_gui.py", "source": root_dir, "dest": root_dir}
    ]
    
    for file_info in files_to_check:
        source_path = os.path.join(file_info["source"], file_info["name"])
        dest_path = os.path.join(file_info["dest"], file_info["name"])
        
        if os.path.exists(source_path) and source_path != dest_path:
            try:
                shutil.copy2(source_path, dest_path)
                print(f"Copied {file_info['name']} to {file_info['dest']}")
            except Exception as e:
                print(f"Warning: Could not copy {file_info['name']}: {e}")
    
    print("\nDirectory structure setup complete!")
    print("\nTo run the SAGE GUI, use the following command:")
    print("    python main_gui.py")
    print("\nMake sure all required dependencies are installed:")
    print("    pip install tkinter pyttsx3 speech_recognition requests opencv-python numpy pyaudio")

if __name__ == "__main__":
    setup_gui_structure()