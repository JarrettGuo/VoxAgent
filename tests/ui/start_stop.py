import sys

from PySide6.QtWidgets import QApplication

from src.ui.main_ui import AssistantWindow
from src.utils.logger import logger

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    g = app.primaryScreen().geometry()

    # Create your voice assistant instance
    # Uncomment when you have your VoiceAssistant class
    # voice_assistant = VoiceAssistant()

    # For testing without VoiceAssistant, use a mock:
    class MockVoiceAssistant:
        def initialize(self):
            import time
            time.sleep(2)  # Simulate initialization
            return True

        def run(self):
            # Simulate running
            import time
            while True:
                time.sleep(1)

        def cleanup(self):
            pass

    voice_assistant = MockVoiceAssistant()

    window = AssistantWindow(voice_assistant, g.width(), g.height())


    sys.exit(app.exec())



if __name__ == '__main__':
    logger.info("start ui test")
    main()
    logger.info("ui test finish")