#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : test_summary_and_tts.py
"""
# test_tts_male_voice.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试男声 TTS
"""

from src.services.tts_client import QiniuTTS
from src.utils.config import config


def main():
    print("=" * 60)
    print("Testing Male Voice TTS")
    print("=" * 60)

    qiniu_config = config.get("qiniu")

    # 创建 TTS 客户端（男声对话）
    print("\n1. Creating TTS client with male voice...")
    tts_client = QiniuTTS(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        voice_type="male_conversation",  # ✅ 男声对话
        encoding="mp3",
        speed_ratio=1.0
    )

    print(f"   Voice ID: {tts_client.voice_id}")
    print(f"   Expected: zh_male_M392_conversation_wvae_bigtts")

    # 测试合成
    print("\n2. Testing synthesize...")
    test_text = "你好，我是语音助手。"

    try:
        audio_data = tts_client.synthesize(
            test_text,
            save_to="/tmp/male_voice_test.mp3"
        )
        print(f"   ✅ Success: {len(audio_data)} bytes")
        print(f"   Saved to: /tmp/male_voice_test.mp3")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return

    # 测试播放
    print("\n3. Testing speak...")
    try:
        tts_client.speak("欢迎使用语音助手系统。")
        print("   ✅ Playback completed")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
