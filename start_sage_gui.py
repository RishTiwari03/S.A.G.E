#!/usr/bin/env python3
# start_sage_gui.py - Launcher for SAGE GUI

import os
import sys
import subprocess

def start_sage_gui():
    """
    Start the SAGE GUI application without creating an infinite loop
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the main_gui.py file
    main_gui_path = os.path.join(script_dir, "gui", "main_gui.py")
    
    # Check if the file exists
    if not os.path.exists(main_gui_path):
        print(f"Error: Could not find {main_gui_path}")
        print("Please make sure the SAGE GUI is properly installed.")
        return False
    
    # Start the GUI
    print("Starting SAGE GUI...")
    try:
        # Use the current Python interpreter to run the script
        python_executable = sys.executable
        
        # Important: Don't use subprocess.run() as it will wait for completion
        # Instead, use subprocess.Popen() and immediately return
        if sys.platform == "win32":
            # Use startupinfo to hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                [python_executable, main_gui_path],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # For other platforms
            process = subprocess.Popen(
                [python_executable, main_gui_path],
                start_new_session=True
            )
        
        # Don't wait for the process - just return success
        return True
    except Exception as e:
        print(f"Error starting SAGE GUI: {e}")
        return False

if __name__ == "__main__":
    # Run once and exit immediately - don't create a loop
    success = start_sage_gui()
    # Exit with appropriate status code
    sys.exit(0 if success else 1)