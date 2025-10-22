#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : agent_entity.py
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent 配置类 - 管理 Agent 的核心配置，包括迭代控制、系统提示词、工具绑定等"""

    # 基础配置
    max_iterations: int = 10  # 最大迭代次数
    enable_memory: bool = True  # 是否启用记忆

    # 提示词配置
    system_prompt: Optional[str] = None  # 系统提示词

    # 工具配置
    tools: List[BaseTool] = Field(default_factory=list)  # 绑定的工具列表

    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True  # 允许任意类型(如 BaseTool)


class AgentState(MessagesState):
    """Agent 状态类 - 继承 LangGraph 的 MessagesState"""

    task_id: UUID  # 任务唯一ID
    iteration_count: int  # 当前迭代次数
    is_finished: bool  # 是否完成
    final_output: Optional[str]  # 最终输出
    history: List[AnyMessage]  # 短期记忆历史
    metadata: Dict[str, Any]  # 额外元数据
