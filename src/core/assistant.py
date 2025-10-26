#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : assistant.py
"""

from typing import Optional

from src.core.audio.recorder import AudioRecorder
from src.core.audio.wake_word_detector import WakeWordDetector
from src.core.initializer import AssistantInitializer
from src.core.processor import CommandProcessor
from src.utils.config import config
from src.utils.logger import logger


class VoiceAssistant:
    """语音助手主类"""

    def __init__(self):
        self.config = config
        self.detector: Optional[WakeWordDetector] = None
        self.recorder: Optional[AudioRecorder] = None
        self.asr_client = None
        self.asr_provider = None
        self.asr_language = None
        self.is_processing = False  # 是否正在处理指令
        self._initialized = False

        # 初始化和处理器
        self.initializer = AssistantInitializer(self)
        self.processor = CommandProcessor(self)

    def initialize(self) -> bool:
        """初始化助手"""
        if self._initialized:
            logger.warning("Assistant is already initialized.")
            return True

        success = self.initializer.initialize_all()
        if success:
            self._initialized = True

        return success

    def _on_wake_detected(self, keyword_index: int):
        """唤醒词检测回调，当检测到唤醒词时调用"""
        if self.is_processing:
            logger.warning("Currently processing, please wait...")
            return

        # 获取唤醒词
        keywords = self.config.get("wake_word.keywords", [])

        # 处理用户指令
        self.processor.process_command()

    def run(self):
        """运行助手"""
        # 初始化
        if not self.initialize():
            logger.error("Assistant initialization failed, exiting...")
            return

        # 显示就绪信息
        self._show_ready_message()

        try:
            # 开始监听唤醒词
            self.detector.start()

        except KeyboardInterrupt:
            logger.info("\nExiting...")

        finally:
            self.cleanup()

    def _show_ready_message(self):
        """显示就绪信息"""
        keywords = self.config.get('wake_word.keywords', [])
        logger.info("Voice Assistant is ready!")
        logger.info(f"Wake words: {', '.join(keywords)}")
        logger.info("press Ctrl+C to exit")

    def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up resources...")

        if self.detector:
            self.detector.cleanup()

        if self.recorder:
            self.recorder.cleanup()

        logger.info("Goodbye!")
