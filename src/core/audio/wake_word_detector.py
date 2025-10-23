#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : wake_word_detector.py
"""

import struct
import time
from typing import Optional, Callable

import pvporcupine
import pyaudio

from src.utils.logger import logger


class WakeWordDetector:
    """唤醒词检测器，监听特定的唤醒词并触发回调"""

    def __init__(
            self,
            access_key: str,
            keywords: list[str],
            sensitivities: Optional[list[float]] = None,
            on_wake: Optional[Callable[[int], None]] = None
    ):
        """初始化唤醒词检测器"""
        self.keywords = keywords
        self.on_wake = on_wake
        self._is_running = False
        self._is_paused = False

        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=keywords,
                sensitivities=sensitivities or [0.5] * len(keywords)
            )
            logger.info(f"   Wake Word: {', '.join(keywords)}")
        except Exception as e:
            logger.error(f"❌ Initializing Porcupine failed: {e}")
            raise

        self.pa = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

    def _open_audio_stream(self):
        """打开音频流，返回 PyAudio Stream 对象"""
        try:
            return self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
        except Exception as e:
            logger.error(f"❌ Failed to open audio stream: {e}")
            raise

    def _close_audio_stream(self):
        """关闭音频流"""
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.warning(f"⚠️  Error closing stream: {e}")
            finally:
                self.stream = None

    def start(self):
        """开始监听唤醒词"""
        if self._is_running:
            logger.warning("Detector is already running.")
            return

        try:
            # 打开音频流
            self.stream = self._open_audio_stream()

            self._is_running = True
            self._is_paused = False
            logger.info("🎤 Started listening for wake words...")
            logger.info(f"   Try saying: {', '.join(self.keywords)}")

            while self._is_running:
                # 如果暂停,跳过处理但继续循环
                if self._is_paused:
                    time.sleep(0.1)  # 暂停时减少CPU占用
                    continue

                try:
                    # 读取音频帧
                    pcm = self.stream.read(
                        self.porcupine.frame_length,
                        exception_on_overflow=False
                    )
                    # 解码音频数据
                    pcm = struct.unpack_from(
                        f"{self.porcupine.frame_length}h",
                        pcm
                    )

                    # 检测唤醒词
                    keyword_index = self.porcupine.process(pcm)

                    if keyword_index >= 0:
                        detected_keyword = self.keywords[keyword_index]
                        logger.info(f"🔔 Detected wake word: '{detected_keyword}'")

                        # 触发回调
                        if self.on_wake:
                            self.on_wake(keyword_index)

                except OSError as e:
                    # 处理音频流可能被暂停时的错误
                    if self._is_paused:
                        continue
                    else:
                        logger.error(f"❌ Audio stream error: {e}")
                        break

        except KeyboardInterrupt:
            logger.info("\n👋 Detected KeyboardInterrupt, stopping...")
        except Exception as e:
            logger.error(f"❌ Error during wake word detection: {e}")
        finally:
            self.stop()

    def pause(self):
        """暂停唤醒词检测 (完全关闭音频流)"""
        if not self._is_running:
            return

        self._is_paused = True

        self._close_audio_stream()
        logger.debug("⏸️  Wake word detection paused (stream closed)")

    def resume(self):
        """恢复唤醒词检测，重新创建音频流"""
        if not self._is_running:
            logger.warning("Cannot resume: detector is not running")
            return

        try:
            # 确保旧流已关闭
            self._close_audio_stream()

            # 等待音频设备完全释放
            time.sleep(0.2)

            # 重新打开音频流
            self.stream = self._open_audio_stream()

            self._is_paused = False
            logger.debug("▶️  Wake word detection resumed (stream recreated)")

        except Exception as e:
            logger.error(f"❌ Failed to resume wake word detection: {e}")
            self._is_paused = True  # 保持暂停状态

    def stop(self):
        """停止监听"""
        self._is_running = False
        self._is_paused = False

        self._close_audio_stream()
        logger.info("🛑 Stopped listening for wake words.")

    def cleanup(self):
        """清理资源"""
        self.stop()

        if self.porcupine:
            try:
                self.porcupine.delete()
                logger.info("🧹 Porcupine resources released")
            except Exception as e:
                logger.error(f"❌ Releasing Porcupine resources failed: {e}")

        if self.pa:
            try:
                self.pa.terminate()
                logger.info("🧹 PyAudio resources released")
            except Exception as e:
                logger.error(f"❌ Releasing PyAudio resources failed: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
