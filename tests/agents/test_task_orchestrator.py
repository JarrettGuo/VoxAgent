# test_edge_tts.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Edge TTS
"""
from src.services.tts_client import tts_client


def test_basic():
    """基础测试"""
    print("=" * 60)
    print("Testing Edge TTS - Basic")
    print("=" * 60)

    # 创建客户端（默认男声）
    print("\n1. Creating EdgeTTS client...")
    tts = tts_client(voice="yunyang")
    print(f"   Voice: {tts.voice_id}")

    # 测试合成
    print("\n2. Testing synthesis...")
    audio_data = tts.synthesize(
        "你好，这是一个语音测试。",
        save_to="/tmp/edge_tts_test.mp3"
    )
    print(f"   ✅ Success: {len(audio_data)} bytes")
    print(f"   Saved to: /tmp/edge_tts_test.mp3")

    # 测试播放
    print("\n3. Testing playback...")
    tts.speak("欢迎使用语音助手。")
    print("   ✅ Playback completed")


def test_different_voices():
    """测试不同音色"""
    print("\n" + "=" * 60)
    print("Testing Different Voices")
    print("=" * 60)

    test_voices = [
        ("yunyang", "云扬 - 男声新闻"),
        ("xiaoxiao", "晓晓 - 女声温柔"),
        ("xiaoyi", "晓伊 - 女声清新"),
    ]

    for voice, description in test_voices:
        print(f"\n📢 Testing: {description}")
        tts = tts_client(voice=voice)
        tts.speak(f"你好，我是{description}。")


def test_speed_control():
    """测试语速控制"""
    print("\n" + "=" * 60)
    print("Testing Speed Control")
    print("=" * 60)

    text = "这是语速测试。"
    speeds = ["-30%", "+0%", "+30%"]

    for speed in speeds:
        print(f"\n🎚️ Speed: {speed}")
        tts = tts_client(voice="yunyang", rate=speed)
        tts.speak(text)


def list_all_voices():
    """列出所有可用音色"""
    print("\n" + "=" * 60)
    print("Available Voices")
    print("=" * 60)

    voices = tts_client.list_voices()

    for key, voice_id in voices.items():
        print(f"  {key:15} -> {voice_id}")


if __name__ == "__main__":
    # 1. 基础测试
    test_basic()

    # 2. 测试不同音色
    test_different_voices()

    # 3. 测试语速
    test_speed_control()

    # 4. 列出所有音色
    list_all_voices()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
