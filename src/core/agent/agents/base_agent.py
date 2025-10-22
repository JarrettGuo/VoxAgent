#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : base_agent.py
"""

import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Iterator, Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, PrivateAttr

from src.core.agent.agents.agent_queue_manager import AgentQueueManager
from src.core.agent.entities.agent_entity import AgentConfig
from src.core.agent.entities.queue_entity import AgentResult, AgentThought
from src.utils.logger import logger


class BaseAgent(BaseModel, Runnable):
    """
    基础 Agent 类 - 适配 LangGraph + 队列管理器

    核心功能：
    1. 继承 Runnable，支持 LangChain 链式调用
    2. 使用 LangGraph 的 StateGraph 构建节点流转
    3. 集成 AgentQueueManager 进行事件发布
    4. 提供同步执行接口 invoke()

    子类需要实现：
    - _build_agent(): 构建 LangGraph 图结构
    """

    # 公开属性
    name: str = "base_agent"  # Agent 名称
    llm: BaseChatModel  # LLM 模型
    config: AgentConfig  # Agent 配置

    # 私有属性（使用 PrivateAttr）
    _agent: Optional[CompiledStateGraph] = PrivateAttr(default=None)
    _queue_manager: Optional[AgentQueueManager] = PrivateAttr(default=None)

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型

    def __init__(
            self,
            name: str,
            llm: BaseChatModel,
            config: Optional[AgentConfig] = None,
            **kwargs
    ):
        """初始化 Agent"""
        super().__init__(
            name=name,
            llm=llm,
            config=config or AgentConfig(),
            **kwargs
        )

        # 初始化私有属性
        self._agent = self._build_agent()
        self._queue_manager = AgentQueueManager()

        logger.info(f"✅ {self.name} initialized")

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        """构建 LangGraph 图结构（子类必须实现）"""
        raise NotImplementedError("Subclass must implement _build_agent()")

    def invoke(
            self,
            input: Dict[str, Any],
            config: Optional[RunnableConfig] = None,
            **kwargs: Any
    ) -> AgentResult:
        """同步执行 Agent（阻塞式，等待完成后返回）"""
        # 1. 提取用户输入
        user_input = input.get("user_input")
        if not user_input:
            raise ValueError("'user_input' is required in input")

        # 2. 创建任务ID
        task_id = uuid.uuid4()

        # 3. 构建初始状态
        initial_state = {
            "task_id": task_id,
            "messages": [HumanMessage(content=user_input)],
            "iteration_count": 0,
            "is_finished": False,
            "final_output": None,
            "history": [],
            "metadata": {}
        }

        logger.info(f"🚀 Starting task {str(task_id)[:8]}... - {user_input}")

        try:
            # 4. 调用 LangGraph 执行
            result = self._agent.invoke(initial_state)

            # 5. 构建返回结果
            final_output = ""
            if result.get("messages"):
                final_output = result["messages"][-1].content

            agent_result = AgentResult(
                task_id=task_id,
                output=final_output,
                is_finished=result.get("is_finished", True),
                iterations=result.get("iteration_count", 0),
                metadata=result.get("metadata", {})
            )

            logger.info(f"✅ Task {str(task_id)[:8]}... completed")
            return agent_result

        except Exception as e:
            logger.error(f"❌ Task {str(task_id)[:8]}... failed: {e}")
            self._queue_manager.publish_error(task_id, e)
            raise

    def stream(
            self,
            input: Dict[str, Any],
            config: Optional[RunnableConfig] = None,
            **kwargs: Any
    ) -> Iterator[AgentThought]:
        """流式执行 Agent（返回事件流）"""
        # 1. 提取用户输入
        user_input = input.get("user_input")
        if not user_input:
            raise ValueError("'user_input' is required in input")

        # 2. 创建任务ID
        task_id = uuid.uuid4()

        # 3. 构建初始状态
        initial_state = {
            "task_id": task_id,
            "messages": [HumanMessage(content=user_input)],
            "iteration_count": 0,
            "is_finished": False,
            "final_output": None,
            "history": [],
            "metadata": {}
        }

        logger.info(f"🚀 Starting streaming task {str(task_id)[:8]}... - {user_input}")

        # 4. 在子线程中执行 Agent
        def execute_agent():
            try:
                self._agent.invoke(initial_state)
            except Exception as e:
                logger.error(f"❌ Agent execution failed: {e}")
                self._queue_manager.publish_error(task_id, e)

        thread = Thread(target=execute_agent)
        thread.start()

        # 5. 监听队列并生成事件流
        try:
            yield from self._queue_manager.listen(task_id)
        finally:
            thread.join()
            logger.info(f"✅ Streaming task {str(task_id)[:8]}... completed")
