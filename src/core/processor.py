#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : processor.py
"""

import time
from typing import TYPE_CHECKING, Dict, Any, Optional, List

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.agents.error_analyzer_agent import ErrorAnalyzerAgent
from src.core.agent.agents.planner_agent import PlannerAgent
from src.core.agent.agents.summary_agent import SummaryAgent
from src.core.agent.agents.task_orchestrator import TaskOrchestrator
from src.core.models import ExecutionPlan
from src.core.processor_modules import (
    AudioHandler,
    ConversationManager,
    ErrorHandler,
    ErrorType
)
from src.core.tools import tool_registry
from src.services.LLMFactory import LLMFactory
from src.services.tts_client import tts_client
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.assistant import VoiceAssistant


class CommandProcessor:
    """命令处理器 - 负责处理用户指令"""

    def __init__(self, assistant: 'VoiceAssistant'):
        self.assistant = assistant
        self.config = assistant.config

        # Agent 实例
        self.llm = None
        self.agents = None
        self.planner = None
        self.orchestrator = None
        self.summarizer = None
        self.error_analyzer = None
        self.tts_client = None

        self._initialized = False

        # 模块实例
        self.audio_handler = AudioHandler(assistant, self.config)
        self.conversation_manager = ConversationManager()
        self.error_handler = None  # 在初始化后创建

        # 语音提示
        self.voice_prompts = {
            "wake": ["请讲"],
            "processing": [
                "好的，请稍等",
                "收到，正在处理",
                "明白了，马上为您处理",
                "好的，稍等片刻"
            ],
            "error": [
                "抱歉，出现了一些问题",
                "很抱歉，处理失败了",
                "抱歉，遇到了错误"
            ]
        }

    def _initialize_system(self) -> bool:
        """初始化整个系统"""
        try:
            # 导入 worker agents 以触发注册
            import src.core.agent.agents.workers.file_agent
            import src.core.agent.agents.workers.search_agent

            registered_types = BaseAgent.get_all_agent_types()
            logger.info(f"Registered agent types: {registered_types}")

            if not registered_types:
                logger.error("No agents registered")
                return False

            # 1. 创建 LLM
            self.llm = self._create_llm()
            if self.llm is None:
                logger.error("Failed to create LLM")
                return False

            # 2. 创建 Worker Agents
            worker_llm = LLMFactory.get_worker_llm()
            self.agents = BaseAgent.create_all_agents(
                llm=worker_llm,
                tool_manager=tool_registry,
                check_dependencies=False
            )

            if not self.agents:
                logger.error("No agents created")
                return False

            logger.info(f"Created {len(self.agents)} agents: {list(self.agents.keys())}")

            # 3. 创建 PlannerAgent
            planner_llm = LLMFactory.get_planner_llm()
            self.planner = PlannerAgent(
                llm=planner_llm,
                available_agents=self.agents
            )
            logger.info("PlannerAgent initialized")

            # 4. 创建 TaskOrchestrator
            self.orchestrator = TaskOrchestrator(agents=self.agents)
            logger.info("TaskOrchestrator initialized")

            # 5. 创建 Summarizer
            summary_llm = LLMFactory.get_summary_llm()
            self.summarizer = SummaryAgent(llm=summary_llm)
            logger.info("SummarizerAgent initialized")

            # 6. 创建 ErrorAnalyzer
            error_llm = LLMFactory.get_summary_llm()
            self.error_analyzer = ErrorAnalyzerAgent(llm=error_llm)
            logger.info("ErrorAnalyzerAgent initialized")

            # 7. 创建 ErrorHandler
            self.error_handler = ErrorHandler(self.error_analyzer)

            # 8. 创建 TTS 客户端
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

    def process_command(self, callback):
        """处理用户指令的主流程"""
    def process_command(self):
        """处理用户指令的主流程（支持多轮对话）"""
        self.assistant.is_processing = True

        try:
            if not self._initialized:
                if not self._initialize_system():
                    self._simple_tts_feedback("系统初始化失败，请稍后重试")
                    return

            # 暂停唤醒词检测
            self.assistant.detector.pause()
            time.sleep(0.2)

            # 播放唤醒确认
            if not self.conversation_manager.state["active"]:
                self._play_wake_confirmation()

            # 1. 录音
            audio_data = self.audio_handler.record_audio()
            if audio_data is None:
                logger.warning("录音被取消或时长不足")

                # 在对话中，检查重试次数
                if self.conversation_manager.state["active"]:
                    retry_count = self.conversation_manager.state.get("empty_audio_retries", 0)

                    if retry_count >= 2:  # 最多重试2次
                        logger.warning("连续录音失败，退出对话")
                        self._simple_tts_feedback("抱歉，没有听到您的声音，请重新唤醒我")
                        self.conversation_manager.reset()
                        return

                    # 增加重试计数
                    self.conversation_manager.state["empty_audio_retries"] = retry_count + 1
                    self._simple_tts_feedback("没有听到声音，请再说一次")
                    time.sleep(0.5)
                    return self.process_command()  # 递归重试
                return

            # 成功录音，清空重试计数
            if self.conversation_manager.state["active"]:
                self.conversation_manager.state["empty_audio_retries"] = 0

            # 2. 语音识别
            text = self.audio_handler.transcribe_audio(audio_data)
            if not text:
                # 识别为空
                if self.conversation_manager.state["active"]:
                    retry_count = self.conversation_manager.state.get("empty_text_retries", 0)

                    if retry_count >= 2:
                        logger.warning("连续识别失败，退出对话")
                        self._simple_tts_feedback("抱歉，无法识别您的语音，请重新唤醒我")
                        self.conversation_manager.reset()
                        return

                    self.conversation_manager.state["empty_text_retries"] = retry_count + 1
                    self._simple_tts_feedback("没有听清楚，请再说一次")
                    time.sleep(0.5)
                    return self.process_command()
                return
            if callback is not None:
                callback(f"User Input: {text}")

            logger.info(f"📝 Recognized text: {text}")

            # 3. 理解意图并规划任务（使用 PlannerAgent）
            execution_plan = self._understand_and_plan(text)

            # 成功识别，清空计数
            if self.conversation_manager.state["active"]:
                self.conversation_manager.state["empty_text_retries"] = 0
            if callback is not None:
                plans = [ plan.description for plan in execution_plan.tasks]
                output = '\n'.join(plans)
                callback(f"Plan Generated:\n {output}")

            # 4. 执行任务计划（使用 TaskOrchestrator）
            execution_result = self._execute_plan(execution_plan)

            # 3. 处理查询
            if self.conversation_manager.state["active"]:
                self._handle_follow_up_input(text)
            else:
                self._handle_new_query(text)
            if callback is not None:
                callback(f"Executed: {execution_result}")

            # 5. 语音反馈
            self._text_to_speech(execution_result)

            logger.info("✅ Processing completed")

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            import traceback
            traceback.print_exc()
            self._simple_tts_feedback("抱歉，处理过程中遇到了错误")
            self.conversation_manager.reset()

        finally:
            self.assistant.is_processing = False

            # 判断是否需要继续对话
            if self.conversation_manager.state["active"]:
                # 检查对话总重试次数
                if self.conversation_manager.max_retries_reached():
                    logger.warning("达到最大重试次数，退出对话")
                    self._simple_tts_feedback("对话次数过多，请重新唤醒我")
                    self.conversation_manager.reset()
                else:
                    # 继续对话
                    logger.info("Conversation active, continuing to listen...")
                    time.sleep(0.5)
                    self.process_command()
            else:
                # 对话结束，恢复唤醒词检测
                time.sleep(0.3)
                logger.info("Resuming wake word detection...")
                self.assistant.detector.resume()
                logger.info("Listening for wake words...\n")

    def _handle_new_query(self, text: str):
        """处理新的用户查询"""
        self.conversation_manager.start_new_query(text)

        self._play_processing_prompt()

        execution_plan = self._understand_and_plan(
            text=text,
            conversation_history=None
        )

        execution_result = self._execute_plan(execution_plan)

        if self._is_execution_successful(execution_result):
            self._finish_execution(text, execution_plan, execution_result)
        else:
            if self._should_retry_with_conversation(execution_result, text):
                self._start_conversation(execution_plan, execution_result)
            else:
                self._finish_execution_with_error(text, execution_plan, execution_result)

    def _start_conversation(
            self,
            execution_plan: ExecutionPlan,
            execution_result: Dict[str, Any]
    ):
        """开始多轮对话"""
        logger.info("Starting conversation")

        self.conversation_manager.activate_conversation(execution_plan)

        original_query = self.conversation_manager.state["original_query"]
        question = self.error_handler.generate_clarification_question(
            execution_result,
            original_query,
            self.conversation_manager.state["messages"]
        )

        # 保存建议
        error_type, error_details = self.error_handler.analyze_error(
            execution_result, original_query
        )
        if error_type == ErrorType.RECOGNITION_ERROR:
            self.conversation_manager.state["suggestion"] = error_details.get("suggestion")

        self.conversation_manager.add_system_response(question)

        logger.info(f"Asking: {question}")
        self._text_to_speech(question)

    def _continue_conversation(
            self,
            execution_plan: ExecutionPlan,
            execution_result: Dict[str, Any]
    ):
        """继续多轮对话"""
        logger.info("Continuing conversation")

        original_query = self.conversation_manager.state["original_query"]
        question = self.error_handler.generate_clarification_question(
            execution_result,
            original_query,
            self.conversation_manager.state["messages"]
        )

        self.conversation_manager.add_system_response(question)

        logger.info(f"Asking: {question}")
        self._text_to_speech(question)

    def _finish_execution(
            self,
            query: str,
            execution_plan: ExecutionPlan,
            execution_result: Dict[str, Any]
    ):
        """完成执行并输出结果"""
        logger.info("Execution finished")

        final_summary = self._generate_final_summary(
            original_query=query,
            execution_plan=execution_plan,
            execution_result=execution_result
        )

        if self.conversation_manager.state["active"]:
            retry_count = self.conversation_manager.state["retry_count"]
            final_summary = f"好的，已为您完成。{final_summary}"
            logger.info(f"Completed after {retry_count} retries")

        self._text_to_speech(final_summary)
        self.conversation_manager.reset()

    def _handle_follow_up_input(self, text: str):
        """处理用户的补充输入"""
        logger.info(f"Follow-up input: {text}")

        self.conversation_manager.add_user_input(text)

        if self.conversation_manager.max_retries_reached():
            logger.warning("Max retries reached")
            self._simple_tts_feedback("抱歉，尝试次数过多，请重新开始")
            self.conversation_manager.reset()
            return

        self._play_processing_prompt()

        # 获取完整对话历史，包括之前的用户输入和系统响应
        conversation_history = self.conversation_manager.get_conversation_history()
        latest_input = self.conversation_manager.get_latest_user_input()

        logger.info(
            f"Conversation history: {len(conversation_history)} messages"
        )

        # 使用对话历史调用 Planner
        execution_plan = self._understand_and_plan(
            text=latest_input,  # 当前输入
            conversation_history=conversation_history
        )

        execution_result = self._execute_plan(execution_plan)

        if self._is_execution_successful(execution_result):
            self._finish_execution(latest_input, execution_plan, execution_result)
        else:
            if self._should_retry_with_conversation(execution_result, latest_input):
                self._continue_conversation(execution_plan, execution_result)
            else:
                self._finish_execution_with_error(latest_input, execution_plan, execution_result)

    def _understand_and_plan(
            self,
            text: str,
            conversation_history: Optional[List] = None
    ) -> ExecutionPlan:
        """理解用户意图并生成执行计划（支持对话历史）"""
        if not self._initialized:
            if not self._initialize_system():
                from uuid import uuid4
                return ExecutionPlan(
                    plan_id=str(uuid4()),
                    tasks=[],
                    dependencies={},
                    metadata={"error": "System not initialized", "feasibility": "error"}
                )

        try:
            # 传递对话历史给 Planner
            execution_plan = self.planner.plan_sync(
                user_query=text,
                conversation_history=conversation_history
            )

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

    def _execute_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """执行任务计划"""
        logger.info("Executing plan...")

        feasibility = execution_plan.metadata.get("feasibility", "unknown")
        reason = execution_plan.metadata.get("reason", "")

        if feasibility != "feasible":
            return {
                "orchestrator_result": None,
                "summary": self._handle_infeasible_plan(feasibility, reason)
            }

        if not execution_plan.tasks:
            return {
                "orchestrator_result": None,
                "summary": "已收到您的指令，但暂时无法生成执行步骤。"
            }

        try:
            plan_dict = self._convert_plan_to_dict(execution_plan)
            orchestrator_result = self.orchestrator.execute(plan_dict)

            return {
                "orchestrator_result": orchestrator_result,
                "summary": None
            }

        except Exception as e:
            logger.error(f"Orchestrator execution failed: {e}", exc_info=True)
            return {
                "orchestrator_result": None,
                "summary": "任务执行过程中出现错误，请稍后重试。"
            }

    def _generate_final_summary(
            self,
            original_query: str,
            execution_plan: ExecutionPlan,
            execution_result: Dict[str, Any]
    ) -> str:
        """生成最终的用户友好总结"""
        if execution_result.get("summary"):
            return execution_result["summary"]

        orchestrator_result = execution_result.get("orchestrator_result")
        if not orchestrator_result:
            return "任务执行遇到了问题，请稍后重试。"

        try:
            logger.info("Generating user-friendly summary...")

            if not self.summarizer:
                logger.warning("Summarizer not initialized, using simple summary")
                return self._create_simple_summary(orchestrator_result)

            summary = self.summarizer.summarize_sync(
                original_query=original_query,
                execution_summary=orchestrator_result
            )

            logger.info(f"Summary generated: {summary[:100]}...")
            return summary

        except Exception as e:
            logger.error(f"Summary generation failed: {e}", exc_info=True)
            return self._create_simple_summary(orchestrator_result)

    @staticmethod
    def _handle_infeasible_plan(feasibility: str, reason: str) -> str:
        """处理不可行的计划"""
        if feasibility == "invalid_input":
            return f"抱歉，我无法理解您的输入。{reason}"
        elif feasibility == "infeasible":
            return f"抱歉，这个任务我目前无法完成。{reason}"
        else:
            return f"收到您的指令，但无法确定如何执行。{reason}"

    @staticmethod
    def _convert_plan_to_dict(execution_plan: ExecutionPlan) -> dict:
        """将 ExecutionPlan 转换为 TaskOrchestrator 需要的字典格式"""
        steps = []
        for task in execution_plan.tasks:
            steps.append({
                "task_id": task.task_id,
                "description": task.description,
                "assigned_agent": task.assigned_agent,
                "expected_result": task.metadata.get("expected_result"),
                "step_number": task.metadata.get("step_number")
            })

        return {
            "steps": steps,
            "plan_id": execution_plan.plan_id,
            "metadata": execution_plan.metadata
        }

    @staticmethod
    def _create_simple_summary(orchestrator_result: Dict[str, Any]) -> str:
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

    def _create_llm(self):
        """创建 LLM 实例"""
        try:
            # 直接使用 LLMFactory
            from src.services.LLMFactory import LLMFactory

            llm = LLMFactory.get_worker_llm()
            logger.info("LLM created successfully via LLMFactory")
            return llm

        except Exception as e:
            logger.error(f"Failed to create LLM: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _play_wake_confirmation(self):
        """播放唤醒确认语音"""
        import random
        prompt = random.choice(self.voice_prompts["wake"])
        logger.info(f"Wake confirmation: {prompt}")
        try:
            if self.tts_client:
                self.tts_client.speak(prompt)
            else:
                logger.info(f"{prompt}")
        except Exception as e:
            logger.error(f"Wake confirmation TTS failed: {e}")

    def _play_processing_prompt(self):
        """播放处理中提示语音"""
        import random
        prompt = random.choice(self.voice_prompts["processing"])
        logger.info(f"Processing prompt: {prompt}")
        try:
            if self.tts_client:
                self.tts_client.speak(prompt)
            else:
                logger.info(f"{prompt}")
        except Exception as e:
            logger.error(f"Processing prompt TTS failed: {e}")

    def _text_to_speech(self, text: str):
        """文字转语音并播放"""
        if not text or not text.strip():
            logger.warning("Empty text for TTS")
            return

        logger.info("Providing voice feedback...")
        logger.info(f"Response: {text}")

        if not self.tts_client:
            logger.warning("TTS client not initialized")
            try:
                edge_config = self.config.get("tts.edge", {})
                self.tts_client = tts_client(
                    voice=edge_config.get("voice", "yunyang"),
                    rate=edge_config.get("rate", "+0%"),
                    volume=edge_config.get("volume", "+0%"),
                    pitch=edge_config.get("pitch", "+0Hz")
                )
                logger.info("TTS client created on-demand")
            except Exception as e:
                logger.error(f"Failed to create TTS client: {e}")
                logger.info("Fallback to text output only")
                return

        try:
            logger.info("Starting speech playback...")
            self.tts_client.speak(text)
            logger.info("Speech playback completed")
        except Exception as e:
            logger.error(f"TTS playback failed: {e}")
            logger.info("Fallback to text output")

    def _simple_tts_feedback(self, message: str):
        """简单的TTS反馈（用于错误情况）"""
        try:
            if self.tts_client:
                self.tts_client.speak(message)
            else:
                logger.info(f"{message}")
        except Exception as e:
            logger.error(f"TTS feedback failed: {e}")

    def _is_execution_successful(self, execution_result: Dict[str, Any]) -> bool:
        """
        判断执行是否成功

        检查：
        1. orchestrator 报告的 success 状态
        2. 每个任务的 status
        3. 结果内容中的失败指示词
        """
        orchestrator_result = execution_result.get("orchestrator_result")

        if not orchestrator_result:
            return False

        # 1. 检查总体状态
        if not orchestrator_result.get("success"):
            return False

        # 2. 检查每个任务的详细结果
        results = orchestrator_result.get("results", [])

        if not results:
            # 没有结果，认为失败
            return False

        for result in results:
            # 2.1 检查任务状态
            status = result.get("status")
            if status in ["failed", "error", "cancelled"]:
                logger.warning(f"Task failed with status: {status}")
                return False

            # 2.2 检查是否有错误信息
            if result.get("error"):
                logger.warning(f"Task has error: {result.get('error')}")
                return False

            # 2.3 检查结果内容
            output = result.get("result", "")

            # 失败指示词（中英文）
            failure_indicators = [
                # 中文
                "未找到", "找不到", "不存在", "失败", "错误",
                "无法", "没有", "无权限", "权限不足",
                # 英文
                "not found", "does not exist", "failed", "error",
                "cannot", "unable", "permission denied",
            ]

            output_lower = str(output).lower()
            for indicator in failure_indicators:
                if indicator in output_lower:
                    logger.warning(
                        f"Task result indicates failure: '{indicator}' "
                        f"found in '{output[:100]}...'"
                    )
                    return False

        # 3. 所有检查通过
        logger.info("All tasks completed successfully")
        return True

    def _should_retry_with_conversation(
            self,
            execution_result: Dict[str, Any],
            original_query: str
    ) -> bool:
        """
        判断是否应该通过多轮对话重试

        1. 基于ErrorHandler的分析
        2. 如果AI生成的提示包含询问意图，也应进入对话
        """
        if not self.error_handler:
            logger.warning("ErrorHandler not available, cannot retry")
            return False

        try:
            # 1. 分析错误类型
            error_type, error_details = self.error_handler.analyze_error(
                execution_result,
                original_query
            )

            logger.info(f"Error analysis: type={error_type.value}")

            # 2. 这些类型直接支持重试
            retriable_types = [
                ErrorType.MISSING_INFO,
                ErrorType.RECOGNITION_ERROR,
            ]

            if error_type in retriable_types:
                return True

            # 3. INVALID_PARAM的特殊处理
            if error_type == ErrorType.INVALID_PARAM:
                # 3.1 有明确的suggestion
                suggestion = error_details.get("suggestion")
                if suggestion:
                    logger.info(f"Found suggestion: {suggestion}")
                    return True

                # 3.2 检查AI生成的提示是否包含询问意图
                try:
                    friendly_message = self.error_handler.generate_clarification_question(
                        execution_result,
                        original_query,
                        self.conversation_manager.state["messages"]
                    )

                    if self._is_asking_for_clarification(friendly_message):
                        logger.info("AI generated a clarification question, entering conversation")
                        # 保存AI生成的问题，避免重复生成
                        self._cached_question = friendly_message
                        return True
                    else:
                        logger.info("INVALID_PARAM without question, cannot retry")
                        return False

                except Exception as e:
                    logger.error(f"Failed to generate clarification question: {e}")
                    return False

            # 4. 其他类型不支持重试
            return False

        except Exception as e:
            logger.error(f"Error analysis failed: {e}", exc_info=True)
            return False

    def _is_asking_for_clarification(self, message: str) -> bool:
        """判断消息是否在询问用户补充信息"""
        question_indicators = [
            # 疑问句标志
            "吗？", "吗?", "？", "?",
            "您是想", "是不是", "对吗",

            # 请求补充
            "请", "请问", "请说明", "请确认",
            "告诉我", "补充", "提供",

            # 选择/列举
            "或", "还是", "或者",
            "哪个", "哪里", "什么",
        ]

        return any(indicator in message for indicator in question_indicators)

    def _finish_execution_with_error(
            self,
            query: str,
            execution_plan: ExecutionPlan,
            execution_result: Dict[str, Any]
    ):
        """
        完成执行（带错误提示）

        用于无法通过多轮对话解决的错误：
        - EXECUTION_FAILED: 权限不足、网络错误等
        - UNKNOWN: 未知错误
        - INVALID_PARAM（无纠正建议）
        """
        logger.info("Execution finished with error")

        # 使用ErrorHandler生成友好提示
        try:
            if self.error_handler:
                friendly_message = self.error_handler.generate_clarification_question(
                    execution_result,
                    query,
                    self.conversation_manager.state["messages"]
                )
            else:
                # 降级：直接使用summary
                friendly_message = execution_result.get("summary", "抱歉，执行过程中遇到了问题。")
        except Exception as e:
            logger.error(f"Failed to generate error message: {e}")
            friendly_message = "抱歉，执行过程中遇到了问题。"

        # TTS播放
        self._text_to_speech(friendly_message)

        # 重置对话状态
        self.conversation_manager.reset()
