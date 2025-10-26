#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : audio_handler.py
"""

import io
import wave
from typing import TYPE_CHECKING

import numpy as np

from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.assistant import VoiceAssistant


class AudioHandler:
    """音频处理模块 - 负责录音、语音识别和音频验证"""

    def __init__(self, assistant: 'VoiceAssistant', config):
        self.assistant = assistant
        self.config = config

    def record_audio(self) -> bytes:
        """录制音频（支持动态时长）"""
        logger.info("Please speak your command...")

        min_duration = self.config.get("recording.dynamic.min_duration", 2.0)
        max_duration = self.config.get("recording.dynamic.max_duration", 60.0)
        silence_threshold = self.config.get("recording.dynamic.silence_threshold", 500.0)
        silence_duration = self.config.get("recording.dynamic.silence_duration", 3.0)
        speech_threshold = self.config.get("recording.dynamic.speech_threshold", 800.0)
        min_speech_chunks = self.config.get("recording.dynamic.min_speech_chunks", 5)

        audio_data = self.assistant.recorder.record_with_silence_detection(
            min_duration=min_duration,
            max_duration=max_duration,
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
            speech_threshold=speech_threshold,
            min_speech_chunks=min_speech_chunks
        )

        return audio_data

    def transcribe_audio(self, audio_data: bytes) -> str:
        """语音识别"""
        logger.info("Converting speech to text...")

        # 检查音频能量
        if not self.has_valid_speech(audio_data):
            logger.warning("Audio contains only silence or noise, skipping transcription")
            return ""

        if self.assistant.asr_provider == "whisper":
            result = self.assistant.asr_client.transcribe_from_bytes(
                audio_data=audio_data,
                audio_format="wav",
                language=self.assistant.asr_language
            )
            text = result.get("text", "").strip()
            text = self.convert_to_simplified(text)
            return text

        elif self.assistant.asr_provider == "qiniu":
            result = self.assistant.asr_client.transcribe(audio_data)
            text = result.get("text", "").strip()
            text = self.convert_to_simplified(text)
            return text

        return ""

    @staticmethod
    def has_valid_speech(audio_data: bytes) -> bool:
        """检查音频是否包含有效语音"""
        try:
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16)

            energy = np.sqrt(np.mean(audio_array.astype(float) ** 2))
            energy_threshold = 100.0

            return energy > energy_threshold

        except Exception as e:
            logger.warning(f"Failed to check audio validity: {e}")
            return True

    @staticmethod
    def convert_to_simplified(text: str) -> str:
        """将繁体中文转换为简体中文"""
        try:
            from opencc import OpenCC
            cc = OpenCC('t2s')
            return cc.convert(text)
        except ImportError:
            logger.warning("OpenCC not installed, returning original text")
            return text
        except Exception as e:
            logger.warning(f"Failed to convert text: {e}")
            return text
