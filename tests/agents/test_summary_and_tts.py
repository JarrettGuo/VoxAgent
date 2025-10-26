#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 SummaryAgent 和 Edge TTS 的集成
"""
from langchain_openai import ChatOpenAI

from src.core.agent.agents.summary_agent import SummaryAgent
from src.services.tts_client import tts_client
from src.utils.config import config
from src.utils.logger import logger


def test_summarizer_and_tts():
    """测试 SummaryAgent + TTS 完整流程"""
    print("=" * 70)
    print("Testing SummaryAgent + TTS Integration")
    print("=" * 70)

    # 1. 初始化 LLM
    print("\n1. Initializing LLM...")
    qiniu_config = config.get("qiniu")
    llm = ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
        temperature=0.7,
    )
    print("   ✅ LLM initialized")

    # 2. 初始化 SummaryAgent
    print("\n2. Initializing SummaryAgent...")
    summarizer = SummaryAgent(llm=llm)
    print("   ✅ SummaryAgent initialized")

    # 3. 初始化 TTS
    print("\n3. Initializing TTS client...")
    edge_config = config.get("tts.edge", {})
    tts = tts_client(
        voice=edge_config.get("voice", "yunyang"),
        rate=edge_config.get("rate", "+0%"),
    )
    print(f"   ✅ TTS initialized (voice={tts.voice_id})")

    # 4. 测试场景
    test_scenarios = [
        {
            "name": "场景1：全部成功",
            "original_query": "搜索Python教程并创建笔记",
            "execution_summary": {
                "success": True,
                "total_steps": 2,
                "successful_steps": 2,
                "failed_steps": 0,
                "results": [
                    {
                        "step": 1,
                        "description": "搜索Python教程",
                        "status": "success",
                        "output": "Python是一种高级编程语言，具有简洁的语法和强大的功能..."
                    },
                    {
                        "step": 2,
                        "description": "创建笔记文件 ~/Desktop/notes.txt",
                        "status": "success",
                        "output": "File created: ~/Desktop/notes.txt"
                    }
                ],
                "error_message": ""
            }
        },
        {
            "name": "场景2：部分失败",
            "original_query": "搜索天气信息并发送邮件",
            "execution_summary": {
                "success": False,
                "total_steps": 2,
                "successful_steps": 1,
                "failed_steps": 1,
                "results": [
                    {
                        "step": 1,
                        "description": "搜索北京天气",
                        "status": "success",
                        "output": "北京今天晴，温度15-25度"
                    },
                    {
                        "step": 2,
                        "description": "发送邮件",
                        "status": "failed",
                        "output": "",
                        "error": "邮件服务未配置"
                    }
                ],
                "error_message": "部分任务执行失败"
            }
        },
        {
            "name": "场景3：全部失败",
            "original_query": "执行不可能的任务",
            "execution_summary": {
                "success": False,
                "total_steps": 1,
                "successful_steps": 0,
                "failed_steps": 1,
                "results": [
                    {
                        "step": 1,
                        "description": "连接到不存在的服务",
                        "status": "failed",
                        "output": "",
                        "error": "服务不可用"
                    }
                ],
                "error_message": "任务执行失败"
            }
        }
    ]

    # 5. 执行测试
    for idx, scenario in enumerate(test_scenarios, 1):
        print("\n" + "=" * 70)
        print(f"📋 {scenario['name']}")
        print("=" * 70)

        original_query = scenario["original_query"]
        execution_summary = scenario["execution_summary"]

        print(f"\n用户问题: {original_query}")
        print(f"执行统计: {execution_summary['successful_steps']}/{execution_summary['total_steps']} 成功")

        # 生成总结
        print("\n⏳ Generating summary...")
        try:
            summary = summarizer.summarize_sync(
                original_query=original_query,
                execution_summary=execution_summary
            )

            print(f"\n📝 Summary generated:")
            print(f"   {summary}")

            # TTS 播放
            print(f"\n🔊 Playing summary via TTS...")
            tts.speak(summary)
            print("   ✅ Playback completed")

        except Exception as e:
            logger.error(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ All summary + TTS tests completed!")
    print("=" * 70)


def test_tts_only():
    """仅测试 TTS 功能"""
    print("\n" + "=" * 70)
    print("Testing TTS Only")
    print("=" * 70)

    # 创建客户端
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
    print("\n" + "=" * 70)
    print("Testing Different Voices")
    print("=" * 70)

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
    print("\n" + "=" * 70)
    print("Testing Speed Control")
    print("=" * 70)

    text = "这是语速测试。"
    speeds = ["-30%", "+0%", "+30%"]

    for speed in speeds:
        print(f"\n🎚️ Speed: {speed}")
        tts = tts_client(voice="yunyang", rate=speed)
        tts.speak(text)


def list_all_voices():
    """列出所有可用音色"""
    print("\n" + "=" * 70)
    print("Available Voices")
    print("=" * 70)

    voices = tts_client.list_voices()

    for key, voice_id in voices.items():
        print(f"  {key:15} -> {voice_id}")


if __name__ == "__main__":
    # 主要测试：SummaryAgent + TTS 集成
    test_summarizer_and_tts()

    # 附加测试
    print("\n\n" + "=" * 70)
    print("Running Additional TTS Tests")
    print("=" * 70)

    # 1. 基础 TTS 测试
    test_tts_only()

    # 2. 测试不同音色
    test_different_voices()

    # 3. 测试语速
    test_speed_control()

    # 4. 列出所有音色
    list_all_voices()

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
