#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : initializer.py
"""

from typing import TYPE_CHECKING

from src.core.audio.recorder import AudioRecorder
from src.core.audio.wake_word_detector import WakeWordDetector
from src.utils.langsmith_setup import setup_langsmith
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.assistant import VoiceAssistant


class AssistantInitializer:
    """助手初始化器 - 负责所有模块的初始化"""

    def __init__(self, assistant: 'VoiceAssistant'):
        self.assistant = assistant
        self.config = assistant.config

    def initialize_all(self) -> bool:
        """初始化所有模块"""
        logger.info("=" * 60)
        logger.info("🤖 VoxAgent Voice Assistant is starting...")
        logger.info("=" * 60)

        self._init_langsmith()

        # 检查配置
        if not self._check_config():
            return False

        # 初始化唤醒词检测器
        if not self._init_wake_word_detector():
            return False

        # 初始化录音模块
        if not self._init_recorder():
            return False

        # 初始化 ASR 客户端
        if not self._init_asr():
            return False

        # TODO: 初始化其他模块
        # - LLM 客户端
        # - TTS 客户端
        # - 工具注册表

        logger.info("✅ All modules initialized successfully")
        return True

    def _init_langsmith(self) -> None:
        """初始化 LangSmith 监控"""
        try:
            setup_langsmith()
        except Exception as e:
            logger.warning(f"LangSmith initialization failed (non-critical): {e}")

    def _check_config(self) -> bool:
        """检查配置是否有效"""
        # 检查唤醒词配置
        access_key = self.config.get("wake_word.access_key")
        if not access_key:
            logger.error("❌ Please configure Porcupine Access Key first")
            return False

        # 检查 ASR 配置
        provider = self.config.get("asr.provider", "whisper").lower()

        if provider == "whisper":
            # Whisper 不需要额外配置检查
            pass
        elif provider == "qiniu":
            # 检查七牛云配置
            api_key = self.config.get("qiniu.api_key")
            if not api_key:
                logger.error("❌ Please configure Qiniu API Key first")
                return False
        # todo 后续的其他配置检查也要放这里

        return True

    def _init_wake_word_detector(self) -> bool:
        """初始化唤醒词检测器"""
        try:
            access_key = self.config.get("wake_word.access_key")
            keywords = self.config.get("wake_word.keywords", ["computer", "jarvis"])
            sensitivities = self.config.get("wake_word.sensitivities", [0.5])

            self.assistant.detector = WakeWordDetector(
                access_key=access_key,
                keywords=keywords,
                sensitivities=sensitivities,
                on_wake=self.assistant._on_wake_detected
            )

            logger.info("✅ Wake word detector initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Wake word detector initialization failed: {e}")
            return False

    def _init_recorder(self) -> bool:
        """初始化录音器"""
        try:
            sample_rate = self.config.get("recording.sample_rate", 16000)
            channels = self.config.get("recording.channels", 1)
            chunk_size = self.config.get("recording.chunk_size", 1024)

            self.assistant.recorder = AudioRecorder(
                sample_rate=sample_rate,
                channels=channels,
                chunk_size=chunk_size
            )

            logger.info("✅ Audio recorder initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Audio recorder initialization failed: {e}")
            return False

    def _init_asr(self) -> bool:
        """初始化 ASR 客户端"""
        try:
            # 获取 ASR 提供商配置
            provider = self.config.get("asr.provider", "whisper").lower()

            if provider == "whisper":
                # 使用本地 Whisper
                from src.services import WhisperASR

                model = self.config.get("asr.whisper.model", "openai/whisper-small")
                device = self.config.get("asr.whisper.device")
                batch_size = self.config.get("asr.whisper.batch_size", 8)
                chunk_length = self.config.get("asr.whisper.chunk_length_s", 30)

                logger.info(f"   Using local Whisper ASR")
                logger.info(f"   Model: {model}")

                self.assistant.asr_client = WhisperASR(
                    model_name=model,
                    device=device,
                    batch_size=batch_size,
                    chunk_length_s=chunk_length
                )
                self.assistant.asr_provider = "whisper"
                self.assistant.asr_language = self.config.get("asr.whisper.language", "zh")
            else:
                logger.error(f"❌ Unknown ASR provider: {provider}")
                return False

            logger.info(f"✅ ASR client initialized (provider: {provider})")
            return True

        except Exception as e:
            logger.error(f"❌ ASR client initialization failed: {e}")
            import traceback
            traceback.print_exc()

            if "No module named" in str(e):
                logger.info("\n💡 Tip: Please install dependencies:")
                logger.info("   pip install torch transformers accelerate")

            return False
