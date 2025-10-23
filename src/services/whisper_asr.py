#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : whisper_asr.py
"""

import os
import subprocess
import tempfile
from typing import Dict, Any, Optional

import torch
from transformers import pipeline

from src.utils.logger import logger


class WhisperASR:
    """
    本地 Whisper 语音识别客户端
    使用 Hugging Face Transformers 实现
    """

    def __init__(
            self,
            model_name: str = "openai/whisper-small",
            device: Optional[str] = None,
            batch_size: int = 8,
            chunk_length_s: int = 30
    ):
        """初始化本地 Whisper ASR"""
        self.model_name = model_name
        self.batch_size = batch_size
        self.chunk_length_s = chunk_length_s

        # 自动选择设备
        if device is None:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"🔄 Initializing Whisper ASR...")

        # 初始化 pipeline
        try:
            self.pipe = pipeline(
                task="automatic-speech-recognition",
                model=model_name,
                chunk_length_s=chunk_length_s,
                device=self.device,
            )
            logger.info("✅ Whisper ASR initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Whisper: {e}")
            logger.info("💡 Tip: First time may need to download model (~1-6GB)")
            raise

    def convert_to_wav(self, input_path: str, target_sr: int = 16000) -> str:
        """将音频文件转换为 WAV 格式"""
        # 创建临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            output_path = temp_file.name

        try:
            # 使用 ffmpeg 转换
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", input_path,
                    "-ar", str(target_sr),  # 采样率
                    "-ac", "1",  # 单声道
                    output_path
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError("Audio conversion failed")

        except FileNotFoundError:
            logger.error("❌ ffmpeg not found. Please install ffmpeg first")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError("ffmpeg not installed")

    def transcribe_from_file(
            self,
            audio_file: str,
            task: str = "transcribe",
            language: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件识别语音"""
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        logger.info(f"🔄 Transcribing audio file: {audio_file}")

        # 检查文件格式
        file_ext = os.path.splitext(audio_file)[1].lower()

        # 如果不是 WAV,先转换
        if file_ext != ".wav":
            logger.info(f"   Converting {file_ext} to WAV...")
            wav_file = self.convert_to_wav(audio_file)
            should_delete = True
        else:
            wav_file = audio_file
            should_delete = False

        try:
            # 构建生成参数
            generate_kwargs = {"task": task}
            if language:
                generate_kwargs["language"] = language

            # 执行识别
            result = self.pipe(
                wav_file,
                batch_size=self.batch_size,
                generate_kwargs=generate_kwargs,
                return_timestamps=True
            )

            text = result["text"].strip()
            logger.info(f"✅ Transcription: {text}")

            return {
                "text": text,
                "chunks": result.get("chunks", []),
                "language": language or "auto"
            }

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise

        finally:
            # 清理临时文件
            if should_delete and os.path.exists(wav_file):
                os.remove(wav_file)

    def transcribe_from_bytes(
            self,
            audio_data: bytes,
            audio_format: str = "wav",
            task: str = "transcribe",
            language: Optional[str] = None
    ) -> Dict[str, Any]:
        """从字节流识别语音"""
        logger.info(f"🔄 Transcribing audio from bytes")
        logger.info(f"   Size: {len(audio_data)} bytes")
        logger.info(f"   Format: {audio_format}")

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False
        ) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            result = self.transcribe_from_file(
                audio_file=temp_path,
                task=task,
                language=language
            )
            return result

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "chunk_length": self.chunk_length_s
        }
