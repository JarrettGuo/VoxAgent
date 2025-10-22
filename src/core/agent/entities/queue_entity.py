#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : queue_entity.py
"""

from enum import Enum
from typing import Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class QueueEvent(str, Enum):
    """队列事件类型枚举"""

    # Agent 核心事件
    AGENT_THOUGHT = "agent_thought"  # Agent 推理过程
    AGENT_MESSAGE = "agent_message"  # Agent 生成消息
    AGENT_ACTION = "agent_action"  # Agent 执行动作(工具调用)
    AGENT_END = "agent_end"  # Agent 执行结束

    # 特殊事件
    ERROR = "error"  # 执行错误
    STOP = "stop"  # 手动停止


class AgentThought(BaseModel):
    """Agent 推理事件数据结构"""

    # 基础标识
    id: UUID  # 事件唯一ID
    task_id: UUID  # 任务ID

    # 事件核心信息
    event: QueueEvent  # 事件类型
    thought: str = ""  # 推理内容(Agent 的思考过程)
    observation: str = ""  # 观察内容(执行结果、环境反馈)

    # 工具相关
    tool: str = ""  # 工具名称
    tool_input: Dict[str, Any] = Field(default_factory=dict)  # 工具输入参数

    # 消息相关
    message: List[Dict[str, Any]] = Field(default_factory=list)  # 消息列表(LangChain 格式)
    answer: str = ""  # 最终答案

    # 性能统计
    latency: float = 0.0  # 延迟时间(秒)

    class Config:
        """Pydantic 配置"""
        use_enum_values = True  # 枚举自动转换为值


class AgentResult(BaseModel):
    """Agent 执行结果"""

    task_id: UUID  # 任务ID
    output: str  # 最终输出
    is_finished: bool  # 是否完成
    iterations: int  # 迭代次数
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据
