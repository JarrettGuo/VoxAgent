#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : conversation_manager.py
"""

from typing import List

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from src.utils.logger import logger


class ConversationManager:
    """对话管理模块 - 基于消息队列"""

    def __init__(self):
        self.state = {
            "active": False,
            "retry_count": 0,
            "max_retries": 3,
            "original_query": None,
            "execution_plan": None,
            "suggestion": None,
            "messages": [],
            "conversation_start_time": None,
            "conversation_timeout": 60,
            "empty_audio_retries": 0,
            "empty_text_retries": 0,
        }

    def reset(self):
        """重置对话状态"""
        logger.info("Resetting conversation state")
        self.state = {
            "active": False,
            "retry_count": 0,
            "max_retries": 3,
            "original_query": None,
            "execution_plan": None,
            "suggestion": None,
            "messages": [],
            "conversation_start_time": None,
            "conversation_timeout": 60,
            "empty_audio_retries": 0,
            "empty_text_retries": 0,
        }

    def start_new_query(self, text: str):
        """开始新查询"""
        logger.info(f"New query: {text}")
        self.reset()
        self.state["original_query"] = text
        self.state["messages"] = [HumanMessage(content=text)]

    def add_user_input(self, text: str):
        """添加用户输入"""
        self.state["messages"].append(HumanMessage(content=text))
        self.state["retry_count"] += 1

    def add_system_response(self, text: str):
        """添加系统响应"""
        self.state["messages"].append(AIMessage(content=text))

    def activate_conversation(self, execution_plan):
        """激活多轮对话"""
        import time
        self.state["active"] = True
        self.state["execution_plan"] = execution_plan
        self.state["retry_count"] = 0
        self.state["conversation_start_time"] = time.time()

    def get_conversation_history(self) -> List[BaseMessage]:
        """获取完整对话历史（供 Planner 使用）"""
        return self.state["messages"]

    def get_latest_user_input(self) -> str:
        """获取最新的用户输入"""
        for msg in reversed(self.state["messages"]):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    def max_retries_reached(self) -> bool:
        """检查是否达到最大重试次数"""
        return self.state["retry_count"] >= self.state["max_retries"]

    def is_conversation_timeout(self) -> bool:
        """检查对话是否超时"""
        if not self.state["active"]:
            return False

        import time
        start_time = self.state.get("conversation_start_time")
        if not start_time:
            return False

        elapsed = time.time() - start_time
        return elapsed > self.state["conversation_timeout"]
