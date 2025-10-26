from PySide6.QtCore import QObject, Signal

class VoiceAssistantWorker(QObject):
    """Worker to run VoiceAssistant in a separate thread"""
    message_received = Signal(str)  # send messages to UI
    initialization_complete = Signal(bool)  # init is done
    status_update = Signal(str)  # status updates

    def __init__(self, voice_assistant):
        super().__init__()
        self.voice_assistant = voice_assistant
        self.running = True

    def run(self):
        """Run the voice assistant"""
        # Initialize
        success = self.voice_assistant.initialize()
        self.initialization_complete.emit(success)

        if not success:
            self.status_update.emit("❌ Initialization failed")
            return

        self.status_update.emit("✨ Voice Assistant ready!")

        # Inject message callback into assistant
        self.voice_assistant.on_message = self.handle_assistant_message

        # Run the assistant (block until stopped)
        try:
            self.voice_assistant.run()
        except Exception as e:
            self.status_update.emit(f"❌ Error: {str(e)}")

    def handle_assistant_message(self, message: str):
        """Callback for when assistant produce a message"""
        self.message_received.emit(message)

    def stop(self):
        """Stop the voice assistant"""
        self.running = False
        if hasattr(self.voice_assistant, 'detector') and self.voice_assistant.detector:
            self.voice_assistant.detector.stop()
        self.voice_assistant.cleanup()