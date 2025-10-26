from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QLabel, QPushButton, QTextEdit, QMenu)
from PySide6.QtCore import Qt, QPointF, QThread
from PySide6.QtGui import QPainter, QColor, QAction
from src.ui.assistant_worker import VoiceAssistantWorker


class FloatingIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Frameless, transparent, always on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(60, 60)
        self.dragging = False
        self.offset = QPointF()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circular icon
        painter.setBrush(QColor(70, 130, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, 50, 50)

        # Draw "AI" text
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "AI")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.position()  # Changed from pos()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging:
            # Changed from pos() to position().toPoint()
            self.move(self.mapToGlobal((event.position() - self.offset).toPoint()))
            # Update main window position if visible
            if self.parent().isVisible():
                self.parent().update_position()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        # Toggle main window
        self.parent().toggle_window()

    def show_context_menu(self, pos):
        menu = QMenu(self)

        # Show/Hide window option
        toggle_action = QAction("Show Window" if not self.parent().isVisible() else "Hide Window", self)
        toggle_action.triggered.connect(self.parent().toggle_window)
        menu.addAction(toggle_action)

        menu.addSeparator()

        # Exit option
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.parent().exit_application)
        menu.addAction(exit_action)

        menu.exec(pos)


class AssistantWindow(QMainWindow):
    def __init__(self, voice_assistant, w, h):
        super().__init__()
        self.setWindowTitle("Desktop Assistant")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(400, 500)

        # Voice assistant integration
        self.voice_assistant = voice_assistant
        self.worker = None
        self.worker_thread = None

        # Setup UI
        self._setup_ui()

        # Create floating icon
        self.floating_icon = FloatingIcon(self)
        self.floating_icon.move(w - 100, h - 300)
        self.floating_icon.show()

        # Start with main window hidden
        self.hide()

        # Start voice assistant in background
        self.start_voice_assistant()

    def _setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("🤖 Desktop Assistant")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)

        # Chat/content area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setText("🔄 Initializing voice assistant...\n\nPlease wait...")
        layout.addWidget(self.chat_area)

        # Input area
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("Type your message here...")
        layout.addWidget(self.input_field)

        # Buttons
        btn_layout = QVBoxLayout()

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        btn_layout.addWidget(send_btn)

        layout.addLayout(btn_layout)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def start_voice_assistant(self):
        """Start the voice assistant in a separate thread"""
        self.worker = VoiceAssistantWorker(self.voice_assistant)
        self.worker_thread = QThread()

        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.message_received.connect(self.display_assistant_message)
        self.worker.initialization_complete.connect(self.on_initialization_complete)
        self.worker.status_update.connect(self.update_status)

        self.worker_thread.start()

    def on_initialization_complete(self, success: bool):
        """Called when voice assistant initialization is complete"""
        if success:
            self.chat_area.clear()
            self.chat_area.append("✨ Voice Assistant is ready!")
            self.chat_area.append("\nDouble-click the floating icon to show/hide this window.")
            self.chat_area.append("Right-click the icon for options.")
            self.chat_area.append("\nSpeak the wake word to activate voice control.")
            self.status_label.setText("✅ Ready")
            self.status_label.setStyleSheet("color: green; padding: 5px;")
        else:
            self.chat_area.clear()
            self.chat_area.append("❌ Failed to initialize voice assistant")
            self.status_label.setText("❌ Initialization failed")
            self.status_label.setStyleSheet("color: red; padding: 5px;")

    def update_status(self, status: str):
        """Update status label"""
        self.status_label.setText(status)

    def display_assistant_message(self, message: str):
        """Display message from voice assistant"""
        self.chat_area.append(f"\n🤖 Assistant: {message}")

    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if message:
            self.chat_area.append(f"\n🧑 You: {message}")
            self.chat_area.append(f"🤖 Assistant: I received your message!")
            self.input_field.clear()

    def update_position(self):
        """Position the main window to the left of the floating icon"""
        icon_pos = self.floating_icon.pos()
        margin = 10  # Space between icon and window

        # Position window to the left of the icon
        new_x = icon_pos.x() - self.width() - margin
        new_y = icon_pos.y() - self.height() + (self.floating_icon.height() // 2)

        # Make sure window doesn't go off-screen
        if new_x < 0:
            # If not enough space on left, put it on the right
            new_x = icon_pos.x() + self.floating_icon.width() + margin
        if new_y < 0:
            # If not enough space on top, put it on the bottom
            new_y = icon_pos.y() + (self.floating_icon.height() // 2)

        self.move(new_x, new_y)

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.update_position()
            self.show()
            self.activateWindow()
            self.raise_()

    def exit_application(self):
        """Properly exit the application"""
        self.chat_area.append("\n👋 Shutting down...")

        # Stop the worker
        if self.worker:
            self.worker.stop()

        # Wait for thread to finish (with timeout)
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(3000)  # Wait max 3 seconds

        # Quit application
        QApplication.quit()