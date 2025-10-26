#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/26/25
@Author : guojarrett@gmail.com
@File   : test_audio_device.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pyaudio
import numpy as np
from src.utils.logger import logger


def diagnose_audio_devices():
    """诊断音频设备和权限"""

    logger.info("=" * 70)
    logger.info("🔍 Audio Device Diagnostic Tool")
    logger.info("=" * 70)

    pa = None

    try:
        pa = pyaudio.PyAudio()

        # 1. 列出所有音频设备
        logger.info("\n📋 Available Audio Devices:")
        logger.info("-" * 70)

        device_count = pa.get_device_count()
        logger.info(f"Total devices found: {device_count}\n")

        for i in range(device_count):
            try:
                info = pa.get_device_info_by_index(i)
                logger.info(f"Device {i}: {info['name']}")
                logger.info(f"  Max Input Channels:  {info['maxInputChannels']}")
                logger.info(f"  Max Output Channels: {info['maxOutputChannels']}")
                logger.info(f"  Default Sample Rate: {int(info['defaultSampleRate'])} Hz")
                logger.info("")
            except Exception as e:
                logger.warning(f"  Cannot read device {i}: {e}\n")

        # 2. 检查默认输入设备
        logger.info("=" * 70)
        logger.info("🎤 Default Input Device Check")
        logger.info("-" * 70)

        try:
            default_input = pa.get_default_input_device_info()
            logger.info(f"✓ Default Input Device Found:")
            logger.info(f"  Name: {default_input['name']}")
            logger.info(f"  Index: {default_input['index']}")
            logger.info(f"  Channels: {default_input['maxInputChannels']}")
            logger.info(f"  Sample Rate: {int(default_input['defaultSampleRate'])} Hz")
        except Exception as e:
            logger.error(f"✗ Cannot get default input device!")
            logger.error(f"  Error: {e}")
            logger.error("\n⚠️  This usually means:")
            logger.error("  1. Microphone permission is NOT granted")
            logger.error("  2. No microphone device available")
            logger.error("\n💡 Solution:")
            logger.error("  Open: System Settings > Privacy & Security > Microphone")
            logger.error("  Grant permission to: Terminal (or your IDE)")
            return False

        # 3. 测试打开音频流
        logger.info("\n" + "=" * 70)
        logger.info("🔧 Audio Stream Test")
        logger.info("-" * 70)

        try:
            logger.info("Attempting to open audio stream...")
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
                input_device_index=default_input['index']
            )
            logger.info("✓ Audio stream opened successfully!")

            # 4. 测试录音
            logger.info("\n📹 Recording Test (2 seconds)...")
            logger.info("Please make some noise or speak now...")

            frames = []
            energy_levels = []

            for i in range(0, int(16000 / 1024 * 2)):
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                    # 计算音频能量
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    rms = np.sqrt(np.mean(np.square(audio_array.astype(np.float64))))
                    energy_levels.append(rms)

                    # 实时显示进度
                    if (i + 1) % 4 == 0:  # 每 0.25 秒显示一次
                        bars = int(rms / 100)
                        logger.info(f"  [{i + 1:2d}/32] Energy: {'█' * min(bars, 50)} {rms:.1f}")

                except Exception as e:
                    logger.error(f"  Error reading frame {i}: {e}")
                    break

            stream.stop_stream()
            stream.close()

            # 5. 分析录音结果
            logger.info("\n" + "-" * 70)
            logger.info("📊 Recording Analysis:")

            if energy_levels:
                avg_energy = np.mean(energy_levels)
                max_energy = np.max(energy_levels)
                min_energy = np.min(energy_levels)

                logger.info(f"  Average Energy: {avg_energy:.1f}")
                logger.info(f"  Max Energy: {max_energy:.1f}")
                logger.info(f"  Min Energy: {min_energy:.1f}")

                # 判断录音质量
                if max_energy < 100:
                    logger.warning("\n⚠️  WARNING: Very low audio signal detected!")
                    logger.warning("  Possible causes:")
                    logger.warning("  1. Microphone volume too low")
                    logger.warning("  2. Microphone is muted")
                    logger.warning("  3. Wrong input device selected")
                    logger.warning("  4. Hardware issue")
                elif avg_energy < 300:
                    logger.warning("\n⚠️  WARNING: Low audio signal")
                    logger.warning("  Try speaking louder or check microphone settings")
                else:
                    logger.info("\n✓ Audio signal looks good!")
                    logger.info(f"  Recorded {len(frames)} frames successfully")
            else:
                logger.error("✗ No audio data captured!")

            # 6. 测试是否能检测到语音
            speech_chunks = sum(1 for e in energy_levels if e > 500)
            logger.info(f"\n  Speech chunks detected (>500): {speech_chunks}")

            if speech_chunks < 5:
                logger.warning("  ⚠️  May not meet min_speech_chunks requirement (default: 5)")
                logger.warning("  Your current thresholds:")
                logger.warning("    - speech_threshold: 800.0")
                logger.warning("    - min_speech_chunks: 5")
                logger.warning("\n  💡 Suggestion: Lower these values in config/config.yaml")
            else:
                logger.info("  ✓ Sufficient speech chunks for detection")

            return True

        except OSError as e:
            logger.error(f"✗ Failed to open audio stream!")
            logger.error(f"  Error: {e}")

            if "err=-50" in str(e) or "Invalid" in str(e):
                logger.error("\n⚠️  Error -50 typically means:")
                logger.error("  1. Microphone permission denied")
                logger.error("  2. Invalid audio device parameters")
                logger.error("  3. Device in use by another application")

            logger.error("\n💡 Solutions:")
            logger.error("  1. Grant microphone permission:")
            logger.error("     System Settings > Privacy & Security > Microphone")
            logger.error("  2. Close other apps using the microphone")
            logger.error("  3. Restart your terminal/IDE")
            logger.error("  4. Try running: sudo killall coreaudiod")
            return False

        except Exception as e:
            logger.error(f"✗ Unexpected error during recording test: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"✗ Failed to initialize PyAudio: {e}")
        return False

    finally:
        if pa:
            try:
                pa.terminate()
                logger.info("\n" + "=" * 70)
                logger.info("✓ PyAudio resources cleaned up")
            except Exception as e:
                logger.warning(f"Warning during cleanup: {e}")

    logger.info("=" * 70)
    return True


def main():
    """主函数"""
    logger.info("\n🚀 Starting Audio Device Diagnostic...")
    logger.info("This tool will help identify audio permission and device issues\n")

    success = diagnose_audio_devices()

    if success:
        logger.info("\n✅ Diagnostic completed successfully!")
        logger.info("If you still have issues, check the warnings above.")
    else:
        logger.error("\n❌ Diagnostic failed!")
        logger.error("Please fix the issues mentioned above and try again.")

    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    main()
