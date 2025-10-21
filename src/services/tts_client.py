#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : tts_client.py
"""
from src.services.qiniu_client import QiniuClient
from src.utils.logger import logger


class QiniuTTS(QiniuClient):
    """
    七牛云语音合成 (TTS) 客户端 (预留接口)
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.endpoint = "/voice/tts"  # 假设端点
        logger.info("✅ 七牛云 TTS 客户端初始化成功")

    def synthesize(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> bytes:
        """
        文本转语音 (待实现)

        Args:
            text: 要合成的文本
            voice: 语音模型

        Returns:
            音频字节数据
        """
        # TODO: 实现 TTS 接口
        logger.info(f"🔄 开始语音合成: {text}")
        raise NotImplementedError("TTS 功能待实现")
