from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QLabel, QPushButton, QTextEdit, QMenu)
from PySide6.QtCore import Qt, QPointF, QThread, QPropertyAnimation, QTimer, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QAction, QRadialGradient, QBrush, QPen, QLinearGradient
from src.ui.assistant_worker import VoiceAssistantWorker


class FloatingIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Frameless, transparent, always on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.color_animation = QPropertyAnimation(self, b"color")
        self.color_animation.setDuration(300)

        self.setFixedSize(100, 100)
        self.dragging = False
        self.offset = QPointF()

        # Color properties for animation
        self._bg_color = QColor(70, 130, 255)  # Default blue
        self._glow_intensity = 0.6
        self._is_listening = False
        self._is_hovered = False

        # Pulse animation for listening state
        self.pulse_value = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_pulse)

        # Scale animation for hover
        self._scale = 1.0
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMouseTracking(True)

    def get_bg_color(self):
        return self._bg_color

    def set_bg_color(self, color):
        self._bg_color = color
        self.update()

    bg_color = Property(QColor, get_bg_color, set_bg_color)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = Property(float, get_scale, set_scale)

    def set_listening(self, listening):
        """Toggle listening state with color change"""
        self._is_listening = listening

        if listening:
            # Animate to purple/pink gradient color
            self.animate_color(QColor(168, 85, 247))  # Purple
            self.pulse_timer.start(50)  # Start pulse animation
        else:
            # Animate back
            self.animate_color(QColor(70, 130, 255))
            self.pulse_timer.stop()
            self.pulse_value = 0.0

        self.update()

    def animate_color(self, target_color):
        """Smoothly transition to target color"""
        animation = QPropertyAnimation(self, b"bg_color")
        animation.setDuration(300)
        animation.setStartValue(self._bg_color)
        animation.setEndValue(target_color)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()

        self._color_animation = animation

    def _update_pulse(self):
        """Update pulse animation value"""
        self.pulse_value += 0.1
        if self.pulse_value > 1.0:
            self.pulse_value = 0.0
        self.update()

    def enterEvent(self, event):
        """Mouse hover - scale up"""
        self._is_hovered = True
        if not self.parent().isVisible():  # Only scale if window is closed
            self.scale_animation.setEndValue(1.1)
            self.scale_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse leave - scale back"""
        self._is_hovered = False
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        icon_radius = 25

        painter.translate(center_x, center_y)
        painter.scale(self._scale, self._scale)
        painter.translate(-center_x, -center_y)

        # Draw outer glow
        if self._glow_intensity > 0:
            glow_gradient = QRadialGradient(center_x, center_y, 45)
            glow_color = QColor(self._bg_color)
            glow_color.setAlpha(int(100 * self._glow_intensity))
            glow_gradient.setColorAt(0, glow_color)
            glow_color.setAlpha(0)
            glow_gradient.setColorAt(1, glow_color)
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(center_x - 45, center_y - 45, 90, 90))

        # Draw pulse ring when listening
        if self._is_listening and self.pulse_value > 0:
            pulse_radius = 25 + (self.pulse_value * 20)
            pulse_alpha = int(150 * (1 - self.pulse_value))
            pulse_color = QColor(self._bg_color)
            pulse_color.setAlpha(pulse_alpha)
            painter.setPen(QPen(pulse_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(center_x - pulse_radius, center_y - pulse_radius,
                                       pulse_radius * 2, pulse_radius * 2))

        # Draw main icon circle with gradient
        gradient = QLinearGradient(center_x - icon_radius, center_y - icon_radius,
                                   center_x + icon_radius, center_y + icon_radius)

        if self._is_listening:
            gradient.setColorAt(0, QColor(168, 85, 247))  # Purple
            gradient.setColorAt(1, QColor(236, 72, 153))  # Pink
        else:
            gradient.setColorAt(0, QColor(59, 130, 246))  # Blue
            gradient.setColorAt(1, QColor(147, 51, 234))  # Purple

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(center_x - icon_radius, center_y - icon_radius,
                                   icon_radius * 2, icon_radius * 2))


        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(center_x - icon_radius, center_y - icon_radius,
                                icon_radius * 2, icon_radius * 2),
                         Qt.AlignmentFlag.AlignCenter, "AI")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.position()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal((event.position() - self.offset).toPoint()))
            if self.parent().isVisible():
                self.parent().update_position()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        self.parent().toggle_window()

    def show_context_menu(self, pos):
        menu = QMenu(self)

        toggle_action = menu.addAction("Show Window" if not self.parent().isVisible() else "Hide Window")
        toggle_action.triggered.connect(self.parent().toggle_window)

        menu.addSeparator()

        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_app)

        menu.exec(pos)

    def exit_app(self):
        QApplication.quit()


class AssistantWindow(QMainWindow):
    def __init__(self, voice_assistant, w, h):
        super().__init__()
        self.setWindowTitle("桌面助手")
        self.resize(400, 500)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.voice_assistant = voice_assistant
        self.worker = None
        self.worker_thread = None

        self._setup_ui()

        self.floating_icon = FloatingIcon(self)
        self.floating_icon.move(w - 100, h - 200)
        self.floating_icon.show()

        self.hide()

        self.start_voice_assistant()

    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 50, 230);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLabel {
                color: white;
                background: transparent;
            }
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🤖 桌面助手")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setText(
            "初始化中...\n")
        layout.addWidget(self.chat_area)

        self.status_label = QLabel("初始化中...")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)


        central.setLayout(layout)
        self.setCentralWidget(central)

    def start_voice_assistant(self):
        """Start the voice assistant in a separate thread"""
        self.worker = VoiceAssistantWorker(self.voice_assistant)
        self.worker_thread = QThread()

        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.initialization_complete.connect(self.on_initialization_complete)
        self.worker.status_update.connect(self.update_status)

        self.worker_thread.start()

    def on_initialization_complete(self, success: bool):
        """Called when voice assistant initialization is complete"""
        if success:
            self.chat_area.clear()
            self.chat_area.append("✨ 准备就绪!")
            self.chat_area.append("你好！我是你的桌面助手\n\n双击图标隐藏/显示浮窗.\n")
            self.chat_area.append("\n说出唤醒词以开始对话")
            self.status_label.setText("✅ OK")
            self.status_label.setStyleSheet("color: green; padding: 5px;")
        else:
            self.chat_area.clear()
            self.chat_area.append("❌ 初始化失败")
            self.status_label.setText("❌ 初始化失败")
            self.status_label.setStyleSheet("color: red; padding: 5px;")

    def update_status(self, status: str):
        """Update status label"""
        self.status_label.setText(status)


    def update_position(self):
        """Position the main window to the left of the floating icon"""
        icon_pos = self.floating_icon.pos()
        margin = 10

        new_x = icon_pos.x() - self.width() - margin
        new_y = icon_pos.y() - self.height() + (self.floating_icon.height() // 2)

        screen_geometry = QApplication.primaryScreen().geometry()

        if new_x < 0:
            new_x = icon_pos.x() + self.floating_icon.width() + margin
        if new_y < 0:
            new_y = 20
        if new_y + self.height() > screen_geometry.height():
            new_y = screen_geometry.height() - self.height() - 20

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
        self.chat_area.append("\n👋 关闭...")

        if self.worker:
            self.worker.stop()

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(3000)

        QApplication.quit()