# -*- mode: python ; coding: utf-8 -*-

import os
import sys
sys.setrecursionlimit(5000)  # Increase recursion limit to help with memory issues

block_cipher = None

# Get current directory
current_dir = os.getcwd()

# List directories and files that definitely exist
# faces_data is inside gui directory, so we don't need to include it separately
datas = [
    ('assistant', 'assistant'),
    ('gui', 'gui'),  # This will include faces_data since it's inside gui
]

# Check for config files and add them if they exist
config_files = ['alarms.json', 'email_config.json', 'weather_config.json', 
               'face_labels.pkl', 'face_recognition_model.yml']
for config_file in config_files:
    if os.path.exists(config_file):
        datas.append((config_file, '.'))

a = Analysis(
    ['gui/main_gui.py'],  # Corrected path to main_gui.py in the gui directory
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'speech_recognition',
        'pyaudio',
        'numpy',
        'PIL._tkinter_finder',
        'win32com',
        'win32com.client',
        'pythoncom',
        'psutil',
        'tkinter',
        'tkinter.filedialog',
        'json',
        'threading',
        'time',
        'os',
        'sys',
        'platform',
        'requests',
        'datetime'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'gtk', 'gi'],  # Exclude unnecessary packages
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SAGE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for final build (no terminal window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sage_icon.ico' if os.path.exists('sage_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python312.dll', 'python*.dll', 'VCRUNTIME*.dll', 'api-ms-*.dll'],
    name='SAGE',
)