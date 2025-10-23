#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : test_wake_word.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.audio.wake_word_detector import WakeWordDetector
from src.utils.config import config
from src.utils.logger import logger


def on_wake_callback(keyword_index: int):
    """唤醒回调函数"""
    keywords = config.get("wake_word.keywords", [])
    keyword = keywords[keyword_index] if keyword_index < len(keywords) else "未知"

    logger.info(f"=" * 50)
    logger.info(f"🎯 触发唤醒: {keyword}")
    logger.info(f"=" * 50)
    # 这里可以添加后续处理逻辑
    # 比如: 开始录音、调用 ASR、处理命令等


def main():
    """测试唤醒词检测"""

    # 读取配置
    access_key = config.get("wake_word.access_key")
    keywords = config.get("wake_word.keywords", ["computer", "jarvis"])
    sensitivities = config.get("wake_word.sensitivities", [0.5, 0.5])

    if not access_key or access_key == "YOUR_PORCUPINE_ACCESS_KEY_HERE":
        logger.error("❌ 请先在 config/config.yaml 中配置 Porcupine Access Key")
        logger.info("   获取方式:")
        logger.info("   1. 访问 https://console.picovoice.ai/")
        logger.info("   2. 注册免费账号")
        logger.info("   3. 复制 Access Key 到配置文件")
        return

    logger.info("🚀 启动唤醒词检测测试...")
    logger.info(f"   监听唤醒词: {', '.join(keywords)}")
    logger.info(f"   灵敏度: {sensitivities}")
    logger.info("")

    # 创建检测器
    try:
        with WakeWordDetector(
                access_key=access_key,
                keywords=keywords,
                sensitivities=sensitivities,
                on_wake=on_wake_callback
        ) as detector:
            # 开始监听
            detector.start()
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
