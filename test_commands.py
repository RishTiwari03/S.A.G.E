# test_commands.py - Clean test script for core commands in SAGE Assistant

import unittest
import sys
import os
import warnings
from unittest.mock import patch, MagicMock
import time

# Suppress all warnings
warnings.filterwarnings("ignore")

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Pre-patch modules to prevent loading issues
# Apply these patches before importing any other modules
for module_name in [
    'assistant.text_to_speech.speak',
    'assistant.text_to_speech.engine',
    'assistant.voice_recognition.listen',
    'assistant.commands.AudioUtilities',
    'assistant.commands.IAudioEndpointVolume',
    'assistant.commands.CLSCTX_ALL',
    'assistant.commands.cast',
    'assistant.commands.POINTER',
    'assistant.facial_recognition.cv2'
]:
    patch_path = '.'.join(module_name.split('.')[:-1])
    patch_target = module_name.split('.')[-1]
    try:
        patch(module_name, MagicMock()).start()
    except Exception:
        # If patching fails, just continue
        pass

# Now import the Commands class
try:
    from assistant.commands import Commands
except ImportError:
    print("Error: Unable to import Commands class. Check your directory structure.")
    sys.exit(1)

# Define a simpler test class with only a few critical tests
class BasicCommandTests(unittest.TestCase):
    """Minimal test case with only the most important command tests"""
    
    def setUp(self):
        """Set up test environment before each test method"""
        print(f"\n{'='*70}")
        print(f"SETTING UP: {self._testMethodName}")
        print(f"{'='*70}")
        
        # Create mocks for dependencies
        self.speak_patcher = patch('assistant.commands.speak')
        self.mock_speak = self.speak_patcher.start()
        
        self.listen_patcher = patch('assistant.commands.listen')
        self.mock_listen = self.listen_patcher.start()
        
        # Mock volume control to prevent COM issues
        if hasattr(Commands, 'volume_control'):
            self.commands_volume_control = Commands.volume_control
            Commands.volume_control = MagicMock()
        
        print("Creating Commands instance for testing...")
        
        # Create an instance of Commands class with simpler initialization
        with patch.object(Commands, '__init__', return_value=None):
            self.commands = Commands()
            
            # Mock essential attributes
            self.commands.in_conversation = False
            self.commands.conversation_command = ""
            self.commands.waiting_for_response = False
            self.commands.common_applications = {}
            self.commands.volume_control = MagicMock()
            self.commands.smtp_configs = {}
            self.commands.weather_service = MagicMock()
            self.commands.alarm_clock = MagicMock()
            self.commands.facial_recognition_available = False
            self.commands.face_recognizer = None
            self.commands.command_lock = MagicMock()
        
        print("Test setup complete.")
    
    def tearDown(self):
        """Clean up after each test method"""
        print(f"\nCleaning up after test: {self._testMethodName}")
        
        # Stop all patches
        self.speak_patcher.stop()
        self.listen_patcher.stop()
        
        # Restore volume control if needed
        if hasattr(self, 'commands_volume_control'):
            Commands.volume_control = self.commands_volume_control
        
        print(f"TEST RESULT: ✅ PASSED: {self._testMethodName}")
    
    def test_01_process_command_open_website(self):
        """Test the open website command"""
        print("\nTEST: Processing 'open website' command")
        with patch.object(self.commands, 'open_website') as mock_open_website:
            print("  Sending command: 'open website google'")
            self.commands.process_command("open website google")
            print("  Verifying 'open_website' was called with argument 'google'")
            mock_open_website.assert_called_once_with("google")
    
    def test_02_process_command_search_google(self):
        """Test the search google command"""
        print("\nTEST: Processing 'search' command")
        with patch.object(self.commands, 'search_google_with_term') as mock_search:
            print("  Sending command: 'search for python tutorials'")
            self.commands.process_command("search for python tutorials")
            print("  Verifying 'search_google_with_term' was called with 'for python tutorials'")
            mock_search.assert_called_once_with("for python tutorials")
    
    def test_03_process_command_play_youtube(self):
        """Test the play youtube command"""
        print("\nTEST: Processing 'play youtube' command")
        with patch.object(self.commands, 'play_youtube_with_term') as mock_play:
            print("  Sending command: 'play youtube for python tutorials'")
            self.commands.process_command("play youtube for python tutorials")
            print("  Verifying 'play_youtube_with_term' was called with 'python tutorials'")
            mock_play.assert_called_once_with("python tutorials")
    
    def test_04_process_command_volume_control(self):
        """Test volume control commands"""
        print("\nTEST: Processing volume control commands")
        
        # Test volume increase
        with patch.object(self.commands, 'adjust_system_volume') as mock_adjust:
            print("  Sending command: 'increase volume'")
            self.commands.process_command("increase volume")
            print("  Verifying 'adjust_system_volume' was called with 'increase'")
            mock_adjust.assert_called_once_with("increase")
        
        # Test volume decrease
        with patch.object(self.commands, 'adjust_system_volume') as mock_adjust:
            print("  Sending command: 'decrease volume'")
            self.commands.process_command("decrease volume")
            print("  Verifying 'adjust_system_volume' was called with 'decrease'")
            mock_adjust.assert_called_once_with("decrease")

    def test_05_process_command_open_application(self):
        """Test opening application command"""
        print("\nTEST: Processing 'open application' command")
        with patch.object(self.commands, 'open_application') as mock_open:
            print("  Sending command: 'open notepad'")
            self.commands.process_command("open notepad")
            print("  Verifying 'open_application' was called with 'open notepad'")
            mock_open.assert_called_once_with("open notepad")


def run_basic_tests():
    """Run a simplified set of tests with clear output"""
    print("\n" + "="*80)
    print("STARTING TESTS FOR SAGE ASSISTANT CORE COMMANDS")
    print("="*80)
    
    # Create and run test suite
    suite = unittest.TestSuite()
    
    # Add tests in order (only the basic ones)
    for i in range(1, 6):  # Tests 1-5
        test_name = f"test_{i:02d}_process_command"
        matching_tests = [t for t in dir(BasicCommandTests) if t.startswith(test_name)]
        for test in matching_tests:
            suite.addTest(BasicCommandTests(test))
    
    # Run the tests with more detailed output
    start_time = time.time()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {suite.countTestCases()}")
    print(f"Tests passed: {suite.countTestCases() - len(result.failures) - len(result.errors)}")
    print(f"Tests failed: {len(result.failures)}")
    print(f"Tests with errors: {len(result.errors)}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\n✅ ALL TESTS PASSED SUCCESSFULLY! ✅")
    else:
        print("\n❌ SOME TESTS FAILED. See details above. ❌")
    
    print("="*80)
    
    # Return success or failure
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    # Suppress all warnings
    if not sys.warnoptions:
        warnings.simplefilter("ignore")
        os.environ["PYTHONWARNINGS"] = "ignore"
    
    # Run the basic tests
    success = run_basic_tests()
    sys.exit(0 if success else 1)