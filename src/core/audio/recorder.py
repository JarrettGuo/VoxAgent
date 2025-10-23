#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : recorder.py
"""

import io
import time
import wave
from typing import Optional

import numpy as np
import pyaudio

from src.utils.logger import logger


class AudioRecorder:
    """音频录制器，支持动态时长录制"""

    def __init__(
            self,
            sample_rate: int = 16000,
            channels: int = 1,
            chunk_size: int = 1024,
            format: int = pyaudio.paInt16
    ):
        """初始化录音器"""
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = format

        self.pa = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.frames = []

        logger.info("✅ Recorder initialized successfully")

    def start_recording(self):
        """开始录音"""
        if self.stream is not None:
            logger.warning("Recording is already in progress.")
            return

        self.frames = []

        try:
            self.stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            logger.info("🎙️  Started recording...")

        except Exception as e:
            logger.error(f"❌ Failed to start recording: {e}")
            raise

    def record_chunk(self) -> bytes:
        """录制一帧音频，返回 PCM 数据"""
        if self.stream is None:
            raise RuntimeError("Recording has not been started.")

        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            self.frames.append(data)
            return data
        except Exception as e:
            logger.error(f"❌ Failed to record chunk: {e}")
            raise

    def stop_recording(self) -> bytes:
        """停止录音并返回 WAV 格式的音频数据"""
        if self.stream is None:
            logger.warning("Recording is not in progress.")
            return b""

        try:
            if self.stream.is_active():
                self.stream.stop_stream()

            self.stream.close()
            self.stream = None

            time.sleep(0.1)

            audio_data = self._frames_to_wav()
            return audio_data

        except Exception as e:
            logger.error(f"❌ Failed to stop recording: {e}")
            raise
        finally:
            self.stream = None

    def _frames_to_wav(self) -> bytes:
        """将录制的帧转换为 WAV 格式"""
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pa.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

        wav_buffer.seek(0)
        return wav_buffer.read()

    @classmethod
    def _calculate_rms(cls, audio_chunk: bytes) -> float:
        """计算音频块的RMS能量值,用于检测静音"""
        try:
            # 检查输入是否为空
            if not audio_chunk or len(audio_chunk) == 0:
                return 0.0

            # 将字节转换为numpy数组
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)

            # 检查数组是否为空
            if len(audio_data) == 0:
                return 0.0

            # 计算均方根,添加保护措施
            mean_square = np.mean(np.square(audio_data.astype(np.float64)))

            # 确保不为负数(理论上不会,但浮点运算可能有误差)
            mean_square = max(0.0, mean_square)

            rms = np.sqrt(mean_square)

            # 检查结果是否有效
            if np.isnan(rms) or np.isinf(rms):
                logger.warning(f"⚠️  Invalid RMS value detected, returning 0.0")
                return 0.0

            return float(rms)

        except Exception as e:
            logger.warning(f"⚠️  Error calculating RMS: {e}, returning 0.0")
            return 0.0

    def record_with_silence_detection(
            self,
            min_duration: float = 2.0,  # 最小时长
            max_duration: float = 60.0,  # 最大时长
            silence_threshold: float = 500.0,  # 静音阈值
            silence_duration: float = 3.0,  # 静音持续时间
            speech_threshold: float = 800.0,  # 语音阈值
            min_speech_chunks: int = 5  # 最少语音帧数
    ) -> Optional[bytes]:
        """动态时长录音,基于静音检测自动停止"""
        logger.info(f"🎙️  Starting dynamic recording (min: {min_duration}s, max: {max_duration}s)...")

        self.start_recording()

        try:
            start_time = time.time()
            last_sound_time = start_time
            chunks_per_second = self.sample_rate // self.chunk_size
            speech_chunks_count = 0  # 计数语音帧

            while True:
                current_time = time.time()
                elapsed = current_time - start_time

                # 检查最大时长
                if elapsed >= max_duration:
                    logger.info(f"⏱️  Reached maximum duration of {max_duration}s")
                    break

                # 录制一帧
                try:
                    chunk = self.record_chunk()
                    if not chunk or len(chunk) == 0:
                        logger.warning("⚠️  Empty audio chunk received, skipping...")
                        continue
                except Exception as e:
                    logger.error(f"❌ Error recording chunk: {e}")
                    break

                # 计算音量
                rms = self._calculate_rms(chunk)

                # 检测是否有明确的语音(更高的阈值)
                if rms > speech_threshold:
                    speech_chunks_count += 1
                    last_sound_time = current_time
                    if int(elapsed) != int(elapsed - 1 / chunks_per_second):
                        logger.debug(f"🎤 Recording speech... {elapsed:.1f}s (RMS: {rms:.1f})")
                elif rms > silence_threshold:
                    # 有声音但不够强,也更新时间
                    last_sound_time = current_time

                # 检查静音时长
                silence_time = current_time - last_sound_time

                # 如果已超过最小时长,且静音超过指定时长,则停止
                if elapsed >= min_duration and silence_time >= silence_duration:
                    logger.info(f"🔇 Detected {silence_time:.1f}s of silence")
                    break

            # 停止录音
            audio_data = self.stop_recording()

            if not audio_data or len(audio_data) == 0:
                logger.warning("⚠️  No audio data recorded")
                return None

            # 检查是否录制到足够的语音
            if speech_chunks_count < min_speech_chunks:
                logger.warning(
                    f"⚠️  Insufficient speech detected ({speech_chunks_count} chunks), likely silence or noise")
                return None

            actual_duration = time.time() - start_time

            if actual_duration < min_duration:
                logger.warning(f"⚠️  Recording too short: {actual_duration:.1f}s")
                return None

            logger.info(f"✅ Recorded {actual_duration:.1f}s with {speech_chunks_count} speech chunks")
            return audio_data

        except Exception as e:
            logger.error(f"❌ Error during recording: {e}")
            import traceback
            traceback.print_exc()
            self.stop_recording()
            raise

    def record_duration(self, duration: float) -> bytes:
        """录制指定时长的音频"""
        logger.info(f"🎙️  Starting to record for {duration} seconds...")

        self.start_recording()

        try:
            num_chunks = int(self.sample_rate / self.chunk_size * duration)

            for i in range(num_chunks):
                self.record_chunk()

                if (i + 1) % (self.sample_rate // self.chunk_size) == 0:
                    elapsed = (i + 1) // (self.sample_rate // self.chunk_size)

            audio_data = self.stop_recording()
            logger.info(f"✅ Finished recording {duration} seconds of audio.")

            return audio_data

        except Exception as e:
            logger.error(f"❌ Error during recording: {e}")
            self.stop_recording()
            raise

    @classmethod
    def save_to_file(cls, audio_data: bytes, filename: str):
        """保存音频到文件"""
        try:
            with open(filename, 'wb') as f:
                f.write(audio_data)

            logger.info(f"💾 Saved audio to file: {filename}")

        except Exception as e:
            logger.error(f"❌ Failed to save audio to file: {e}")
            raise

    def cleanup(self):
        """清理资源"""
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            finally:
                self.stream = None

        if self.pa:
            try:
                self.pa.terminate()
                logger.info("🧹 AudioRecorder resources cleaned up.")
            except:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
