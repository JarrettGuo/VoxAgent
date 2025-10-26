#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/26/25
@Author : guojarrett@gmail.com
@File   : test_processor_modules.py
"""

import io
import wave
from unittest.mock import Mock

import numpy as np
import pytest

from src.core.processor_modules import (
    AudioHandler,
    ConversationManager,
    ErrorHandler,
    ErrorType
)


class TestAudioHandler:
    """AudioHandler 核心功能测试"""

    @pytest.fixture
    def mock_assistant(self):
        """创建 mock assistant"""
        assistant = Mock()
        assistant.config = Mock()
        assistant.recorder = Mock()
        assistant.asr_client = Mock()
        assistant.asr_provider = "whisper"
        assistant.asr_language = "zh"

        assistant.config.get = Mock(side_effect=lambda key, default=None: {
            "recording.dynamic.min_duration": 2.0,
            "recording.dynamic.max_duration": 60.0,
        }.get(key, default))

        return assistant

    def test_record_audio_success(self, mock_assistant):
        """✅ 测试成功录音"""
        handler = AudioHandler(mock_assistant, mock_assistant.config)
        mock_assistant.recorder.record_with_silence_detection.return_value = b"audio_data"

        result = handler.record_audio()

        assert result == b"audio_data"

    def test_transcribe_audio_success(self, mock_assistant):
        """✅ 测试转录成功"""
        handler = AudioHandler(mock_assistant, mock_assistant.config)
        audio_data = self._create_valid_audio()
        mock_assistant.asr_client.transcribe_from_bytes.return_value = {
            "text": "测试文本"
        }

        result = handler.transcribe_audio(audio_data)

        assert result == "测试文本"

    def test_transcribe_audio_silence_detection(self, mock_assistant):
        """🔇 测试静音检测"""
        handler = AudioHandler(mock_assistant, mock_assistant.config)
        silent_audio = self._create_silent_audio()

        result = handler.transcribe_audio(silent_audio)

        assert result == ""

    @staticmethod
    def _create_valid_audio():
        """创建有效音频数据"""
        sample_rate = 16000
        t = np.linspace(0, 1.0, sample_rate)
        audio_signal = (np.sin(2 * np.pi * 440 * t) * 5000).astype(np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_signal.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()

    @staticmethod
    def _create_silent_audio():
        """创建静音音频"""
        sample_rate = 16000
        audio_signal = (np.random.randn(sample_rate) * 10).astype(np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_signal.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()


class TestConversationManager:
    """ConversationManager 核心功能测试"""

    def test_start_new_query(self):
        """✅ 测试开始新查询"""
        manager = ConversationManager()
        manager.start_new_query("查询天气")

        assert manager.state["original_query"] == "查询天气"
        assert len(manager.state["messages"]) == 1

    def test_conversation_flow(self):
        """💬 测试对话流程"""
        manager = ConversationManager()

        manager.start_new_query("查询天气")
        manager.add_system_response("请问要查询哪个城市？")
        manager.activate_conversation(Mock())
        manager.add_user_input("北京")

        assert manager.state["active"] is True
        assert manager.state["retry_count"] == 1
        assert len(manager.state["messages"]) == 3

    def test_merge_query_simple(self):
        """✅ 测试简单查询合并"""
        manager = ConversationManager()
        manager.start_new_query("查询天气")
        manager.add_user_input("北京")

        merged = manager.merge_query_for_planner()

        assert "天气" in merged
        assert "北京" in merged

    def test_needs_more_info(self):
        """❓ 测试判断是否需要更多信息"""
        manager = ConversationManager()

        # 情况1：缺少参数
        result = {
            "orchestrator_result": {
                "success": False,
                "error_message": "未指定城市"
            }
        }
        assert manager.needs_more_info(result) is True

        # 情况2：执行成功
        result = {
            "orchestrator_result": {
                "success": True
            }
        }
        assert manager.needs_more_info(result) is False


class TestErrorHandler:
    """ErrorHandler 核心功能测试"""

    @pytest.fixture
    def error_handler(self):
        """创建 ErrorHandler 实例"""
        return ErrorHandler(Mock())

    def test_analyze_error_missing_info(self, error_handler):
        """🔍 测试识别缺失信息错误"""
        execution_result = {
            "orchestrator_result": {
                "success": False,
                "results": [{
                    "status": "failed",
                    "error": "未指定城市",
                    "description": "查询天气"
                }]
            }
        }

        error_type, details = error_handler.analyze_error(execution_result, "查询天气")

        assert error_type == ErrorType.MISSING_INFO

    def test_analyze_error_invalid_param(self, error_handler):
        """🔍 测试识别无效参数错误"""
        execution_result = {
            "orchestrator_result": {
                "success": False,
                "results": [{
                    "status": "failed",
                    "error": "未找到城市'xyz'",
                    "description": "查询天气"
                }]
            }
        }

        error_type, _ = error_handler.analyze_error(execution_result, "查询xyz天气")

        assert error_type in [ErrorType.RECOGNITION_ERROR, ErrorType.INVALID_PARAM]

    def test_suggest_correction_city(self, error_handler):
        """💡 测试城市名纠正建议"""
        suggestion = error_handler.suggest_correction(
            "查询波士炖天气",
            "未找到城市'波士炖'",
            "查询天气"
        )

        assert suggestion == "波士顿"

    def test_generate_clarification_question(self, error_handler):
        """💬 测试生成友好提示"""
        # Mock analyzer 返回字符串
        error_handler.error_analyzer.analyze_error_with_history_sync.return_value = "请问要查询哪个城市？"

        execution_result = {
            "orchestrator_result": {
                "success": False,
                "results": [{
                    "status": "failed",
                    "error": "未指定城市",
                    "description": "查询天气"
                }]
            }
        }

        question = error_handler.generate_clarification_question(
            execution_result,
            "查询天气",
            []
        )

        assert isinstance(question, str)
        assert len(question) > 0


class TestIntegration:
    """模块集成测试"""

    def test_full_conversation_with_correction(self):
        """🔄 测试完整的对话和纠正流程"""
        manager = ConversationManager()
        error_handler = ErrorHandler(Mock())

        manager.start_new_query("查询波士炖天气")

        execution_result = {
            "orchestrator_result": {
                "success": False,
                "results": [{
                    "status": "failed",
                    "error": "Don't find city: 波士炖",
                    "description": "查询天气"
                }]
            }
        }

        error_type, details = error_handler.analyze_error(
            execution_result,
            "查询波士炖天气"
        )

        if error_type == ErrorType.RECOGNITION_ERROR:
            assert details.get("suggestion") == "波士顿"

            manager.activate_conversation(Mock())
            manager.state["suggestion"] = details.get("suggestion")
            manager.add_system_response("您是想查询波士顿的天气吗？")

            manager.add_user_input("是")
            merged = manager.merge_query_for_planner()

            assert "波士顿" in merged or "波士炖" not in merged


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
