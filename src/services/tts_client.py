#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : tts_client.py
"""

import asyncio
import io
from typing import Optional

import edge_tts
from pydub import AudioSegment
from pydub.playback import play

from src.utils.logger import logger


class tts_client:
    """Edge TTS 客户端（基于微软 Edge 浏览器的 TTS）"""

    # 中文音色列表
    VOICES = {
        # 普通话 - 女声
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 晓晓（温柔）
        "xiaoyi": "zh-CN-XiaoyiNeural",  # 晓伊（清新）
        "xiaoyou": "zh-CN-XiaoyouNeural",  # 晓悠（少女）
        "yunxi": "zh-CN-YunxiNeural",  # 云希（温暖女声）
        "yunxia": "zh-CN-YunxiaNeural",  # 云霞（成熟）

        # 普通话 - 男声
        "yunyang": "zh-CN-YunyangNeural",  # 云扬（新闻男声）
        "yunjian": "zh-CN-YunjianNeural",  # 云健（运动）
        "yunhao": "zh-CN-YunhaoNeural",  # 云皓（广告）

        # 其他方言
        "hiugaai": "zh-HK-HiuGaaiNeural",  # 粤语 - 女声
        "wanlung": "zh-HK-WanLungNeural",  # 粤语 - 男声
        "hsiaoyou": "zh-TW-HsiaoyouNeural",  # 台湾 - 女声
        "yunjhe": "zh-TW-YunjheNeural",  # 台湾 - 男声
    }

    def __init__(
            self,
            voice: str = "yunyang",  # 默认：云扬（男声）
            rate: str = "+0%",  # 语速：-50% 到 +100%
            volume: str = "+0%",  # 音量：-50% 到 +50%
            pitch: str = "+0Hz"  # 音高：-50Hz 到 +50Hz
    ):
        """初始化 Edge TTS 客户端"""
        self.voice_id = self.VOICES.get(voice, self.VOICES["yunyang"])
        self.rate = rate
        self.volume = volume
        self.pitch = pitch

        logger.info(f"EdgeTTS initialized (voice={self.voice_id}, rate={rate})")

    async def synthesize_async(
            self,
            text: str,
            save_to: Optional[str] = None
    ) -> bytes:
        """异步合成语音 - 返回音频数据 (MP3)"""
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return b""

        logger.info(f"Synthesizing speech: {text[:50]}...")

        try:
            # 创建 TTS 通信对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice_id,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch
            )

            # 合成音频
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            # 保存到文件
            if save_to:
                with open(save_to, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"Audio saved to: {save_to}")

            logger.info(f"Speech synthesis completed ({len(audio_data)} bytes)")
            return audio_data

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise

    def synthesize(
            self,
            text: str,
            save_to: Optional[str] = None
    ) -> bytes:
        """同步合成语音 - 返回音频数据 (MP3)"""
        return asyncio.run(self.synthesize_async(text, save_to))

    def speak(self, text: str) -> None:
        """合成并播放语音"""
        try:
            # 合成音频
            audio_data = self.synthesize(text)

            if not audio_data:
                logger.warning("No audio data to play")
                return

            logger.info("Playing audio...")

            # 播放音频
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            play(audio)

            logger.info("Audio playback completed")

        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            raise

    @classmethod
    def list_voices(cls) -> dict:
        """列出所有可用音色"""
        return cls.VOICES

    @classmethod
    async def list_all_voices_async(cls) -> list:
        """异步获取所有可用音色（包括详细信息）"""
        voices = await edge_tts.list_voices()
        # 筛选中文音色
        chinese_voices = [
            v for v in voices
            if v["Locale"].startswith("zh-")
        ]
        return chinese_voices

    @classmethod
    def list_all_voices(cls) -> list:
        """同步获取所有可用音色"""
        return asyncio.run(cls.list_all_voices_async())
