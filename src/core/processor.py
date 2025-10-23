#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : processor.py
"""
import io
import time
import wave
from typing import TYPE_CHECKING, Dict, Any

import numpy as np
from langchain_openai import ChatOpenAI

from src.core.agent.agents.planner_agent import PlannerAgent
from src.core.agent.entities.agent_entity import AgentConfig
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.assistant import VoiceAssistant


class CommandProcessor:
    """命令处理器 - 负责处理用户指令"""

    def __init__(self, assistant: 'VoiceAssistant'):
        self.assistant = assistant
        self.config = assistant.config
        self.planner_agent = None  # PlannerAgent 实例（延迟初始化）

    def process_command(self):
        """处理用户指令的主流程"""
        self.assistant.is_processing = True

        try:
            # 暂停唤醒词检测,避免麦克风冲突
            logger.info("⏸️  Pausing wake word detection...")
            self.assistant.detector.pause()

            # 等待一小段时间,确保麦克风释放
            time.sleep(0.2)

            # 1. 录音
            audio_data = self._record_audio()
            if audio_data is None:
                logger.warning("⚠️  录音被取消或时长不足，跳过处理")
                return

            # 2. 语音识别 (ASR)
            text = self._transcribe_audio(audio_data)
            if not text:
                return

            logger.info(f"📝 Recognized text: {text}")

            # 3. 理解意图并规划任务（使用 PlannerAgent）
            plan_result = self._understand_and_plan(text)

            # 4. 执行任务计划
            execution_result = self._execute_plan(plan_result)

            # 5. 语音反馈
            self._text_to_speech(execution_result)

            logger.info("✅ Processing completed")

        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.assistant.is_processing = False

            # 等待录音器完全释放资源
            time.sleep(0.3)

            # 恢复唤醒词检测
            logger.info("▶️  Resuming wake word detection...")
            self.assistant.detector.resume()

            logger.info("🎤 Listening for wake words...\n")

    def _record_audio(self) -> bytes:
        """录制音频（支持动态时长）"""
        logger.info("🎙️  Please speak your command...")
        min_duration = self.config.get("recording.dynamic.min_duration", 2.0)
        max_duration = self.config.get("recording.dynamic.max_duration", 60.0)
        silence_threshold = self.config.get("recording.dynamic.silence_threshold", 500.0)
        silence_duration = self.config.get("recording.dynamic.silence_duration", 3.0)
        speech_threshold = self.config.get("recording.dynamic.speech_threshold", 800.0)
        min_speech_chunks = self.config.get("recording.dynamic.min_speech_chunks", 5)

        audio_data = self.assistant.recorder.record_with_silence_detection(
            min_duration=min_duration,
            max_duration=max_duration,
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
            speech_threshold=speech_threshold,
            min_speech_chunks=min_speech_chunks
        )

        return audio_data

    def _transcribe_audio(self, audio_data: bytes) -> str:
        """语音识别"""
        logger.info("🔄 Converting speech to text...")

        # 检查音频能量,过滤掉纯静音
        if not self._has_valid_speech(audio_data):
            logger.warning("⚠️  Audio contains only silence or noise, skipping transcription")
            return ""

        if self.assistant.asr_provider == "whisper":
            # 本地 Whisper
            result = self.assistant.asr_client.transcribe_from_bytes(
                audio_data=audio_data,
                audio_format="wav",
                language=self.assistant.asr_language
            )
            return result.get("text", "").strip()

        elif self.assistant.asr_provider == "qiniu":
            # 七牛云 ASR
            result = self.assistant.asr_client.transcribe(audio_data)
            return result.get("text", "").strip()

        return ""

    def _has_valid_speech(self, audio_data: bytes) -> bool:
        """检查音频是否包含有效语音"""

        try:
            # 将 bytes 转换为音频数组
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16)

            # 计算能量
            energy = np.sqrt(np.mean(audio_array.astype(float) ** 2))

            # 能量阈值
            energy_threshold = 100.0

            return energy > energy_threshold

        except Exception as e:
            logger.warning(f"⚠️ Failed to check audio validity: {e}")
            return True

    def _understand_and_plan(self, text: str) -> Dict[str, Any]:
        """
        理解意图并生成执行计划（使用 PlannerAgent）

        参数:
            text: 用户的语音识别文本

        返回:
            包含计划的字典
        """
        logger.info("🧠 Understanding intent and planning...")

        # 1. 初始化 PlannerAgent
        if self.planner_agent is None:
            self.planner_agent = self._initialize_planner_agent()

        # todo 如果失败，调用tts模型输出
        # if self.planner_agent is None:

        # 3. 使用 PlannerAgent 生成计划
        try:
            plan_result = self.planner_agent.plan_task(text)
            logger.info(f"📋 Plan generated: {plan_result.get('plan', {}).get('feasibility', 'unknown')}")

            logger.info("Plan Details:", plan_result.get("plan", {}))

            return plan_result

        except Exception as e:
            logger.error(f"❌ Planning failed: {e}")
            return {
                "success": False,
                "message": f"规划任务时出错: {str(e)}",
                "plan": {
                    "task": text,
                    "feasibility": "error",
                    "steps": []
                }
            }

    def _initialize_planner_agent(self):
        """初始化 PlannerAgent"""
        try:
            # 获取配置
            max_iterations = self.config.get("agent.planner.max_iterations", 5)

            # 创建 LLM
            llm = self._create_llm()
            if llm is None:
                logger.warning("⚠️ Failed to create LLM, PlannerAgent disabled")
                return None

            # 创建配置
            config = AgentConfig(
                max_iterations=max_iterations,
                enable_memory=False,
            )

            # 创建 PlannerAgent
            agent = PlannerAgent(
                name="planner_agent",
                llm=llm,
                config=config,
            )

            logger.info("✅ PlannerAgent initialized successfully")
            return agent

        except Exception as e:
            logger.error(f"❌ Failed to initialize PlannerAgent: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_llm(self):
        """创建 LLM 实例"""
        try:
            # 尝试从七牛云配置创建
            qiniu_config = self.config.get("qiniu")
            if qiniu_config:
                llm = ChatOpenAI(
                    api_key=qiniu_config.get("api_key"),
                    base_url=qiniu_config.get("base_url"),
                    model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
                    temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
                    max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
                )

                logger.info("✅ LLM created from Qiniu config")
                return llm

        except ImportError:
            logger.warning("⚠️ langchain_openai not installed")
        except Exception as e:
            logger.error(f"❌ Failed to create LLM: {e}")

        return None

    def _execute_plan(self, plan_result: Dict[str, Any]) -> str:
        """
        执行任务计划

        参数:
            plan_result: PlannerAgent 返回的计划结果

        返回:
            执行结果描述
        """
        logger.info("⚙️  Executing plan...")

        # 1. 检查计划是否成功
        if not plan_result.get("success"):
            return plan_result.get("message", "规划失败")

        # 2. 获取计划
        plan = plan_result.get("plan", {})

        # 3. 检查可行性
        feasibility = plan.get("feasibility", "unknown")

        if feasibility == "invalid_input":
            # todo 交给tts模型输出
            return "您的输入似乎不够清晰，请重新表述您的需求。"

        elif feasibility == "infeasible":
            # todo 交给tts模型输出
            return "抱歉，这个任务我目前无法完成。我只能执行计算机相关的操作。"

        elif feasibility == "feasible":
            steps = plan.get("steps", [])
            if not steps:
                return "已收到您的指令，但暂时无法执行。"

            # TODO: 实际执行步骤
            # 这里可以调用工具系统执行具体步骤
            logger.info(f"📝 Plan has {len(steps)} steps")
            logger.info("   (Actual execution to be implemented)")

            return f"我已经为您规划了 {len(steps)} 个步骤，但目前还不支持自动执行。"

        else:
            return "收到您的指令，但无法确定如何执行。"

    def _text_to_speech(self, text: str):
        """文字转语音"""
        # TODO: 调用 TTS API
        logger.info("🔊 Providing voice feedback...")
        logger.info(f"💬 Response: {text}")
