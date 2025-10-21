#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : processor.py
"""

import time
from typing import TYPE_CHECKING

from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.assistant import VoiceAssistant


class CommandProcessor:
    """命令处理器 - 负责处理用户指令"""

    def __init__(self, assistant: 'VoiceAssistant'):
        self.assistant = assistant
        self.config = assistant.config

    def process_command(self):
        """处理用户指令的主流程"""
        self.assistant.is_processing = True

        try:
            # 暂停唤醒词检测,避免麦克风冲突
            logger.info("⏸️  Pausing wake word detection...")
            self.assistant.detector.pause()

            # 等待一小段时间,确保麦克风释放
            time.sleep(0.2)

            # 1. 录音
            audio_data = self._record_audio()
            if audio_data is None:
                logger.warning("⚠️  录音被取消或时长不足，跳过处理")
                return

            # 2. 语音识别 (ASR)
            text = self._transcribe_audio(audio_data)
            if not text:
                return

            logger.info(f"📝 Recognized text: {text}")

            # 3. 理解意图并规划任务
            plan = self._understand_and_plan(text)

            # 4. 执行任务
            result = self._execute_plan(plan)

            # 5. 语音反馈
            self._text_to_speech(result)

            logger.info("✅ Processing completed")

        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.assistant.is_processing = False

            # 等待录音器完全释放资源
            time.sleep(0.3)

            # 恢复唤醒词检测
            logger.info("▶️  Resuming wake word detection...")
            self.assistant.detector.resume()

            logger.info("🎤 Listening for wake words...\n")

    def _record_audio(self) -> bytes:
        """录制音频（支持动态时长）"""
        logger.info("🎙️  Please speak your command...")
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

    def _transcribe_audio(self, audio_data: bytes) -> str:
        """语音识别"""
        logger.info("🔄 Converting speech to text...")

        # 检查音频能量,过滤掉纯静音
        if not self._has_valid_speech(audio_data):
            logger.warning("⚠️  Audio contains only silence or noise, skipping transcription")
            return ""

        if self.assistant.asr_provider == "whisper":
            # 本地 Whisper
            result = self.assistant.asr_client.transcribe_from_bytes(
                audio_data=audio_data,
                audio_format="wav",
                language=self.assistant.asr_language
            )
        else:
            # 七牛云 (需要 URL,这里会失败)
            logger.error("❌ Qiniu ASR requires URL, not supported for realtime")
            return ""

        text = result.get("text", "").strip()

        if not text:
            logger.warning("⚠️  No speech detected or recognized")
            return ""

        # 过滤 Whisper 的常见幻觉输出
        if self._is_hallucination(text):
            logger.warning(f"⚠️  Detected hallucination output: '{text}', ignoring")
            return ""

        return text

    def _has_valid_speech(self, audio_data: bytes, threshold: float = 100.0) -> bool:
        """检查音频是否包含有效语音(基于RMS能量)"""
        import numpy as np
        import wave
        import io

        try:
            # 读取 WAV 数据
            with wave.open(io.BytesIO(audio_data), 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16)

            # 计算整体 RMS
            rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))

            logger.debug(f"   Audio RMS: {rms:.1f}, threshold: {threshold}")

            return rms > threshold

        except Exception as e:
            logger.warning(f"⚠️  Error checking audio energy: {e}")
            return True  # 出错时允许继续识别

    @classmethod
    def _is_hallucination(cls, text: str) -> bool:
        """检测是否为 Whisper 的幻觉输出"""
        # 常见的 Whisper 幻觉模式
        hallucination_patterns = [
            "字幕",
            "翻译",
            "谢谢观看",
            "请不吝点赞",
            "订阅",
            "关注",
            "by",
            "感谢",
            "我们下期再见",
            "拜拜",
            "索兰娅",
            "subtitle",
            "amara",
            "字幕组",
            # 可以根据实际情况添加更多
        ]

        text_lower = text.lower()

        # 检查是否包含幻觉关键词
        for pattern in hallucination_patterns:
            if pattern in text_lower:
                return True

        # 检查长度(真实语音通常不会太短)
        if len(text.strip()) < 2:
            return True

        return False

    def _understand_and_plan(self, text: str) -> dict:
        """理解意图并生成执行计划"""
        # TODO: 调用 LLM 进行意图理解和任务规划
        logger.info("🧠 Understanding intent and planning...")
        logger.info(f"   User said: {text}")

        return {
            "intent": "unknown",
            "text": text,
            "actions": []
        }

    def _execute_plan(self, plan: dict) -> str:
        """执行任务计划"""
        # TODO: 调用工具执行任务
        logger.info("⚙️  Executing plan...")
        text = plan.get("text", "")
        return f"Received your command: {text}"

    def _text_to_speech(self, text: str):
        """文字转语音"""
        # TODO: 调用 TTS API
        logger.info("🔊 Providing voice feedback...")
        logger.info(f"💬 Response: {text}")
