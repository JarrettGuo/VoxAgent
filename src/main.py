#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : main.py
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.ui.main_ui import AssistantWindow

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.assistant import VoiceAssistant

def main():
    app = QApplication(sys.argv)
    g = app.primaryScreen().geometry()
    app.setQuitOnLastWindowClosed(False)

    assistant = VoiceAssistant()
    window = AssistantWindow(assistant, g.width(), g.height())
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
