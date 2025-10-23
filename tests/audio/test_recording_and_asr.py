#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : test_recording_and_asr.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.audio.recorder import AudioRecorder
from src.services import WhisperASR
from src.utils.config import config
from src.utils.logger import logger


def test_whisper_asr():
    """测试 Whisper ASR"""

    logger.info("=" * 60)
    logger.info("🧪 测试本地 Whisper ASR")
    logger.info("=" * 60)

    # 1. 初始化 Whisper
    logger.info("\n初始化 Whisper...")
    model = config.get("asr.whisper.model", "openai/whisper-small")
    language = config.get("asr.whisper.language", "zh")

    logger.info(f"   模型: {model}")
    logger.info(f"   语言: {language}")
    logger.info("   首次运行会下载模型,请耐心等待...")

    try:
        asr = WhisperASR(model_name=model)
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        return

    # 2. 初始化录音器
    logger.info("\n初始化录音器...")
    recorder = AudioRecorder()

    # 3. 录音
    duration = config.get("recording.duration", 5)
    logger.info(f"\n准备录音 {duration} 秒...")
    logger.info("请说话! 例如: '今天天气怎么样'")
    logger.info("")

    try:
        audio_data = recorder.record_duration(duration)

        # 保存录音
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "whisper_test.wav"
        recorder.save_to_file(audio_data, str(output_file))

        # 4. 识别
        logger.info("\n开始识别...")
        result = asr.transcribe_from_bytes(
            audio_data=audio_data,
            audio_format="wav",
            language=language
        )

        # 5. 显示结果
        text = result.get("text", "")
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎯 识别结果")
        logger.info("=" * 60)
        logger.info(f"文本: {text}")
        logger.info(f"语言: {result.get('language', 'auto')}")
        logger.info(f"录音: {output_file}")
        logger.info("=" * 60)

        # 显示时间戳(如果有)
        chunks = result.get("chunks", [])
        if chunks:
            logger.info("\n时间戳:")
            for chunk in chunks[:5]:  # 只显示前5个
                timestamp = chunk.get("timestamp", [0, 0])
                text = chunk.get("text", "")
                logger.info(f"  [{timestamp[0]:.2f}s - {timestamp[1]:.2f}s] {text}")

    except KeyboardInterrupt:
        logger.info("\n测试被中断")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        recorder.cleanup()


if __name__ == "__main__":
    test_whisper_asr()
