#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : error_analyzer_agent.py
"""

from typing import Optional, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from src.core.agent.entities.agent_prompts import ERROR_ANALYZER_SYSTEM_PROMPT
from src.utils.logger import logger


class ErrorAnalyzerAgent:
    """错误分析 Agent - 结合对话历史和错误信息生成友好提示"""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        logger.info("ErrorAnalyzerAgent initialized")

    def analyze_error_with_history_sync(
            self,
            conversation_history: List[BaseMessage],
            original_query: str,
            task_description: str,
            error_message: str,
            error_type: str,
            suggestion: Optional[str] = None
    ) -> str:
        """结合对话历史分析错误并生成友好提示"""
        try:
            # 构建包含历史对话的输入
            input_data = self._format_input_with_history(
                conversation_history,
                original_query,
                task_description,
                error_message,
                error_type,
                suggestion
            )

            # 构建完整消息链
            messages = [
                SystemMessage(content=ERROR_ANALYZER_SYSTEM_PROMPT),
                *conversation_history,
                HumanMessage(content=input_data)
            ]

            logger.info(f"Analyzing error with {len(conversation_history)} history messages")
            self._log_conversation(conversation_history)

            # 调用 LLM
            response = self.llm.invoke(messages)
            friendly_message = response.content.strip()

            logger.info(f"Generated friendly error message: {friendly_message}")
            return friendly_message

        except Exception as e:
            logger.error(f"Error analysis failed: {e}", exc_info=True)
            return self._create_fallback_message(error_type, error_message)

    def _format_input_with_history(
            self,
            conversation_history: List[BaseMessage],
            original_query: str,
            task_description: str,
            error_message: str,
            error_type: str,
            suggestion: Optional[str]
    ) -> str:
        """格式化输入（历史对话已在消息链中，这里只需当前错误信息）"""

        prompt = f"""
【当前执行情况】

**用户最新输入：**
{original_query}

**执行任务：**
{task_description}

**错误信息：**
{error_message}

**错误类型：**
{error_type}
"""

        if suggestion:
            prompt += f"""
**建议纠正：**
{suggestion}
"""

        prompt += """
---

请根据以上对话历史和当前错误信息，生成简洁、友好的语音提示（1-2句话）：
"""

        return prompt

    def _log_conversation(self, messages: List[BaseMessage]):
        """打印对话历史（调试用）"""
        if not messages:
            return

        logger.debug("=" * 60)
        logger.debug("Conversation History:")
        for i, msg in enumerate(messages, 1):
            role = "User" if isinstance(msg, HumanMessage) else "AI"
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            logger.debug(f"{i}. {role}: {content}")
        logger.debug("=" * 60)

    def _create_fallback_message(
            self,
            error_type: str,
            error_message: str
    ) -> str:
        """降级方案：生成简单的错误提示"""
        fallback_templates = {
            "missing_info": "抱歉，缺少必要的信息。请补充说明。",
            "recognition_error": "语音识别可能有误，请重新说明。",
            "invalid_param": "提供的信息有误，请重新说明。",
            "execution_failed": "执行遇到问题，请稍后重试。",
            "unknown": "抱歉，遇到了一些问题。请重新描述您的需求。"
        }

        message = fallback_templates.get(error_type, fallback_templates["unknown"])

        if len(error_message) < 50:
            message = f"{error_message}。请重新说明。"

        return message
