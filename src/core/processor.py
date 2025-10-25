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

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.agents.planner_agent import PlannerAgent
from src.core.agent.agents.summary_agent import SummaryAgent
from src.core.agent.agents.task_orchestrator import TaskOrchestrator
from src.core.models import ExecutionPlan
from src.core.tools import tool_registry
from src.services.tts_client import tts_client
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.assistant import VoiceAssistant


class CommandProcessor:
    """命令处理器 - 负责处理用户指令"""

    def __init__(self, assistant: 'VoiceAssistant'):
        self.assistant = assistant
        self.config = assistant.config

        self.llm = None  # LLM 实例
        self.agents = None  # Worker Agents 字典
        self.planner = None  # PlannerAgent 实例
        self.orchestrator = None  # TaskOrchestrator 实例
        self.summary = None  # summary Agent 实例
        self.tts_client = None  # TTS 客户端实例

        self._initialized = False

    def _initialize_system(self) -> bool:
        """
        初始化整个系统：LLM, Agents, Planner, Orchestrator
        """
        try:
            # 导入 worker agents 以触发注册
            import src.core.agent.agents.workers.file_agent
            import src.core.agent.agents.workers.search_agent

            # 验证注册
            registered_types = BaseAgent.get_all_agent_types()
            logger.info(f"Registered agent types: {registered_types}")

            if not registered_types:
                logger.error("No agents registered")
                return False

            # 1. 创建 LLM 实例
            self.llm = self._create_llm()
            if self.llm is None:
                logger.error("Failed to create LLM")
                return False

            # 2. 创建 Worker Agents
            self.agents = BaseAgent.create_all_agents(
                llm=self.llm,
                tool_manager=tool_registry,
                check_dependencies=False
            )

            if not self.agents:
                logger.error("No agents created")
                return False

            logger.info(f"Created {len(self.agents)} agents: {list(self.agents.keys())}")

            # 3. 创建 PlannerAgent
            self.planner = PlannerAgent(
                llm=self.llm,
                available_agents=self.agents
            )
            logger.info("PlannerAgent initialized")

            # 4. 创建 TaskOrchestrator
            self.orchestrator = TaskOrchestrator(agents=self.agents)
            logger.info("TaskOrchestrator initialized")

            # 创建 Summarizer
            self.summarizer = SummaryAgent(llm=self.llm)
            logger.info("SummarizerAgent initialized")

            # 创建 TTS 客户端
            edge_config = self.config.get("tts.edge", {})
            self.tts_client = tts_client(
                voice=edge_config.get("voice", "yunyang"),
                rate=edge_config.get("rate", "+0%"),
                volume=edge_config.get("volume", "+0%"),
                pitch=edge_config.get("pitch", "+0Hz")
            )

            self._initialized = True
            logger.info("System initialized successfully")
            return True

        except Exception as e:
            logger.error(f"System initialization failed: {e}", exc_info=True)
            return False

    def process_command(self):
        """处理用户指令的主流程"""
        self.assistant.is_processing = True

        try:
            if not self._initialized:
                logger.info("🔄 First-time initialization...")
                if not self._initialize_system():
                    logger.error("❌ System initialization failed")
                    self._simple_tts_feedback("系统初始化失败，请稍后重试")
                    return

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
            execution_plan = self._understand_and_plan(text)

            # 4. 执行任务计划（使用 TaskOrchestrator）
            execution_result = self._execute_plan(execution_plan)

            # 5. 总结结果（新增）
            final_summary = self._generate_final_summary(
                original_query=text,
                execution_plan=execution_plan,
                execution_result=execution_result
            )

            # 6. 语音输出（更新）
            self._text_to_speech(final_summary)

        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
            self._simple_tts_feedback("抱歉，处理过程中遇到了错误")

        finally:
            self.assistant.is_processing = False

            # 等待录音器完全释放资源
            time.sleep(0.3)
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
            text = result.get("text", "").strip()

            # 繁体转简体
            text = self._convert_to_simplified(text)
            return text

        elif self.assistant.asr_provider == "qiniu":
            # 七牛云 ASR
            result = self.assistant.asr_client.transcribe(audio_data)
            text = result.get("text", "").strip()

            # 添加繁体转简体
            text = self._convert_to_simplified(text)
            return text

        return ""

    def _convert_to_simplified(self, text: str) -> str:
        """将繁体中文转换为简体中文"""
        try:
            from opencc import OpenCC
            cc = OpenCC('t2s')  # 繁体转简体
            return cc.convert(text)
        except ImportError:
            logger.warning("⚠️  OpenCC not installed, returning original text")
            logger.info("   Install with: pip install opencc-python-reimplemented")
            return text
        except Exception as e:
            logger.warning(f"⚠️  Failed to convert text: {e}")
            return text

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

    def _understand_and_plan(self, text: str) -> ExecutionPlan:
        """
        理解用户意图并生成执行计划
        """
        # 1. 初始化系统
        if not self._initialized:
            if not self._initialize_system():
                from uuid import uuid4
                return ExecutionPlan(
                    plan_id=str(uuid4()),
                    tasks=[],
                    dependencies={},
                    metadata={
                        "error": "System not initialized",
                        "feasibility": "error"
                    }
                )

        try:
            # 使用 PlannerAgent 生成执行计划
            execution_plan = self.planner.plan_sync(text)

            # 日志输出
            feasibility = execution_plan.metadata.get("feasibility", "unknown")
            logger.info(
                f"Plan generated: {len(execution_plan.tasks)} tasks, "
                f"feasibility={feasibility}"
            )

            return execution_plan

        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)

            from uuid import uuid4
            return ExecutionPlan(
                plan_id=str(uuid4()),
                tasks=[],
                dependencies={},
                metadata={
                    "error": str(e),
                    "original_query": text,
                    "feasibility": "error"
                }
            )

    def _create_llm(self):
        """创建 LLM 实例"""
        try:
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

    def _execute_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """
        执行任务计划（使用 TaskOrchestrator）
        """
        logger.info("⚙️  Executing plan...")

        feasibility = execution_plan.metadata.get("feasibility", "unknown")
        reason = execution_plan.metadata.get("reason", "")

        # 1. 处理不可行的情况
        if feasibility != "feasible":
            return {
                "orchestrator_result": None,
                "summary": self._handle_infeasible_plan(feasibility, reason)
            }

        # 2. 检查是否有任务
        if not execution_plan.tasks:
            return {
                "orchestrator_result": None,
                "summary": "已收到您的指令，但暂时无法生成执行步骤。"
            }

        # 3. 使用 TaskOrchestrator 执行计划
        try:
            plan_dict = self._convert_plan_to_dict(execution_plan)
            orchestrator_result = self.orchestrator.execute(plan_dict)

            return {
                "orchestrator_result": orchestrator_result,
                "summary": None  # 稍后生成
            }

        except Exception as e:
            logger.error(f"❌ Orchestrator execution failed: {e}", exc_info=True)
            return {
                "orchestrator_result": None,
                "summary": f"执行过程中出现错误：{str(e)}"
            }

    def _handle_infeasible_plan(self, feasibility: str, reason: str) -> str:
        """处理不可行的计划"""
        if feasibility == "invalid_input":
            return f"抱歉，我无法理解您的输入。{reason}"
        elif feasibility == "infeasible":
            return f"抱歉，这个任务我目前无法完成。{reason}"
        else:
            return f"收到您的指令，但无法确定如何执行。{reason}"

    def _convert_plan_to_dict(self, execution_plan: ExecutionPlan) -> dict:
        """
        将 ExecutionPlan 转换为 TaskOrchestrator 需要的字典格式
        """
        steps = []
        for task in execution_plan.tasks:
            steps.append({
                "task_id": task.task_id,
                "description": task.description,
                "assigned_agent": task.assigned_agent,
                "parameters": task.parameters,
                "expected_result": task.metadata.get("expected_result"),
                "step_number": task.metadata.get("step_number")
            })

        return {
            "steps": steps,
            "plan_id": execution_plan.plan_id,
            "metadata": execution_plan.metadata
        }

    def _format_orchestrator_result(self, orchestrator_result: dict, reason: str = "") -> str:
        """
        格式化 TaskOrchestrator 的执行结果为用户友好的反馈
        """
        success = orchestrator_result.get("success", False)
        total_steps = orchestrator_result.get("total_steps", 0)
        successful_steps = orchestrator_result.get("successful_steps", 0)
        failed_steps = orchestrator_result.get("failed_steps", 0)
        results = orchestrator_result.get("results", [])
        error_message = orchestrator_result.get("error_message", "")

        # 构建摘要
        summary_parts = []

        # 1. 总体情况
        if success:
            summary_parts.append(f"✅ 成功完成所有 {total_steps} 个任务！")
        elif successful_steps == 0:
            summary_parts.append(f"❌ 很抱歉，所有任务都执行失败了。")
        else:
            summary_parts.append(
                f"⚠️  部分完成：成功 {successful_steps}/{total_steps} 个任务，"
                f"失败 {failed_steps} 个任务。"
            )

        # 2. 成功任务的输出
        successful_results = [r for r in results if r.get("status") == "success"]
        if successful_results:
            summary_parts.append("\n📋 执行结果：")
            for i, result in enumerate(successful_results, 1):
                description = result.get("description", "")
                # 从 result 中提取输出
                task_result = result.get("result", {})
                output = task_result.get("output", "") if isinstance(task_result, dict) else str(task_result)

                # 截断过长的输出
                if len(output) > 200:
                    output = output[:200] + "..."

                summary_parts.append(f"{i}. {description}\n   结果: {output}")

        # 3. 失败任务的错误信息
        failed_results = [r for r in results if r.get("status") == "failed"]
        if failed_results:
            summary_parts.append("\n❌ 失败任务：")
            for i, result in enumerate(failed_results, 1):
                description = result.get("description", "")
                error = result.get("error", "Unknown error")
                summary_parts.append(
                    f"{i}. {description}\n"
                    f"   错误: {error}"
                )

        # 4. 整体错误信息
        if error_message and not failed_results:
            summary_parts.append(f"\n❌ 错误: {error_message}")

        # 5. 规划原因（如果有）
        if reason:
            summary_parts.append(f"\n💡 任务分析：{reason}")

        return "\n".join(summary_parts)

    def _text_to_speech(self, text: str):
        """文字转语音并播放"""
        if not text or not text.strip():
            logger.warning("Empty text for TTS")
            return

        logger.info("🔊 Providing voice feedback...")
        logger.info(f"💬 Response: {text}")

        # 确保TTS客户端可用
        if not self.tts_client:
            logger.warning("⚠️  TTS client not initialized")
            # 尝试创建TTS客户端
            try:
                edge_config = self.config.get("tts.edge", {})
                self.tts_client = tts_client(
                    voice=edge_config.get("voice", "yunyang"),
                    rate=edge_config.get("rate", "+0%"),
                    volume=edge_config.get("volume", "+0%"),
                    pitch=edge_config.get("pitch", "+0Hz")
                )
                logger.info("✅ TTS client created on-demand")
            except Exception as e:
                logger.error(f"❌ Failed to create TTS client: {e}")
                logger.info("💬 Fallback to text output only")
                return

        # 播放语音
        try:
            logger.info("🔊 Starting speech playback...")
            self.tts_client.speak(text)
            logger.info("✅ Speech playback completed")
        except Exception as e:
            logger.error(f"❌ TTS playback failed: {e}")
            logger.info("💬 Fallback to text output")

    def _generate_final_summary(
            self,
            original_query: str,
            execution_plan: ExecutionPlan,
            execution_result: Dict[str, Any]
    ) -> str:
        """生成最终的用户友好总结"""
        # 如果已经有预生成的总结（不可行的情况），直接返回
        if execution_result.get("summary"):
            return execution_result["summary"]

        # 获取 orchestrator 的执行摘要
        orchestrator_result = execution_result.get("orchestrator_result")
        if not orchestrator_result:
            return "任务执行遇到了问题，请稍后重试。"

        # 使用 Summarizer Agent 生成总结
        try:
            logger.info("📝 Generating user-friendly summary...")

            # 确保summarizer已初始化
            if not self.summarizer:
                logger.warning("⚠️  Summarizer not initialized, using simple summary")
                return self._create_simple_summary(orchestrator_result)

            summary = self.summarizer.summarize_sync(
                original_query=original_query,
                execution_summary=orchestrator_result
            )

            logger.info(f"✅ Summary generated: {summary[:100]}...")
            return summary

        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}", exc_info=True)
            # 降级方案
            return self._create_simple_summary(orchestrator_result)

    def _create_simple_summary(self, orchestrator_result: Dict[str, Any]) -> str:
        """创建简单的总结（降级方案）"""
        success = orchestrator_result.get("success", False)
        total_steps = orchestrator_result.get("total_steps", 0)
        successful_steps = orchestrator_result.get("successful_steps", 0)

        if success:
            return f"好的，我已经完成了所有{total_steps}个任务。"
        elif successful_steps == 0:
            return "抱歉，任务执行失败了。"
        else:
            failed = total_steps - successful_steps
            return f"我完成了{successful_steps}个任务，但还有{failed}个任务未能完成。"

    def _simple_tts_feedback(self, message: str):
        """简单的TTS反馈（用于错误情况）"""
        try:
            if self.tts_client:
                self.tts_client.speak(message)
            else:
                logger.info(f"💬 {message}")
        except Exception as e:
            logger.error(f"❌ TTS feedback failed: {e}")
