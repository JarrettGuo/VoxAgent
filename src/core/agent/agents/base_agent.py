#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : base_agent.py
"""
import asyncio
import platform
from abc import ABC
from typing import Optional, Dict, ClassVar, Type, List, Any

from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool

from src.core.agent.entities.agent_entity import AgentMetadata, AgentConfig
from src.core.tools import ToolRegistry
from src.utils.logger import logger


class BaseAgent(Runnable, ABC):
    """基础 Agent 类，所有具体 Agent 的基类"""
    _registry: ClassVar[Dict[str, Type['BaseAgent']]] = {}
    _metadata: ClassVar[Dict[str, AgentMetadata]] = {}

    # 子类必须定义的类属性
    agent_name: ClassVar[str] = "base_agent"
    agent_description: ClassVar[str] = "基础 Agent 类"
    agent_system_prompt: ClassVar[str] = "你是一个智能代理，负责处理用户请求。"

    def __init_subclass__(
            cls,
            agent_type: str = None,
            priority: int = 50,
            platforms: Optional[List[str]] = None,
            required_tools: Optional[List[str]] = None,
            enabled: bool = True,
            **kwargs
    ):
        """自动注册子类，并进行平台兼容性检查"""
        super().__init_subclass__(**kwargs)

        if not agent_type:
            return

        # 验证子类是否定义了必需的类属性
        if cls.agent_name is None:
            raise TypeError(f"{cls.__name__} must define 'agent_name' class attribute")
        if cls.agent_description is None:
            raise TypeError(f"{cls.__name__} must define 'agent_description' class attribute")
        if cls.agent_system_prompt is None:
            raise TypeError(f"{cls.__name__} must define 'agent_system_prompt' class attribute")

        # 创建元数据，用于注册和管理
        metadata = AgentMetadata(
            agent_type=agent_type,
            priority=priority,
            platforms=platforms,
            required_tools=required_tools,
            enabled=enabled
        )

        # 平台兼容性检查
        if not metadata.is_platform_compatible():
            logger.info(
                f"Skipping {cls.__name__}: "
                f"not compatible with {platform.system()}"
            )
            return

        # 注册
        cls._registry[agent_type] = cls
        cls._metadata[agent_type] = metadata

        logger.info(
            f"Registered: {agent_type} -> {cls.__name__} "
            f"(priority={priority}, platforms={platforms or 'all'})"
        )

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """生成动态系统 prompt - 子类可以重写此方法来实现自定义的动态 prompt 生成逻辑"""
        return cls.agent_system_prompt

    def __init__(
            self,
            llm: BaseChatModel,
            tool_manager: ToolRegistry,
            config: Optional[AgentConfig] = None
    ):
        """初始化 Agent，子类不需要重写此方法，所有配置通过类属性自动获取。"""
        super().__init__()

        # 获取当前类的元数据
        agent_type = self._get_agent_type()
        metadata = self._metadata.get(agent_type)

        if not metadata:
            raise ValueError(f"Agent type {agent_type} not found in registry")

        # 自动获取工具
        self.tools = self._get_tools(tool_manager, metadata.required_tools)

        # 初始化配置
        self.llm = llm
        self.config = config or AgentConfig()

        # 绑定工具到 LLM
        self.llm_with_tools = llm.bind_tools(self.tools)

        # 生成动态系统 prompt
        system_prompt = self.__class__.generate_system_prompt(self.tools)

        # 构建 Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        agent = create_openai_tools_agent(
            llm=llm,
            tools=self.tools,
            prompt=self.prompt
        )

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            max_iterations=self.config.max_iterations,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            verbose=False,
        )

        # 初始化对话历史
        self.conversation_history: List[BaseMessage] = []

        logger.info(
            f"Initialized {self.__class__.agent_name} with {len(self.tools)} tools"
        )

    def _get_agent_type(self) -> str:
        """获取当前 Agent 的类型"""
        for agent_type, agent_class in self._registry.items():
            if isinstance(self, agent_class):
                return agent_type
        raise ValueError(f"Agent {self.__class__.__name__} not registered")

    def _get_tools(
            self,
            tool_manager: ToolRegistry,
            required_tools: Optional[List[str]]
    ) -> List[BaseTool]:
        """自动获取工具"""
        if not required_tools:
            return []

        try:
            return tool_manager.get_tools_by_names(required_tools)
        except ValueError as e:
            logger.error(f"Failed to get tools: {e}")
            raise

    def reset(self):
        """重置对话历史"""
        self.conversation_history = []

    async def ainvoke(
            self,
            input: Dict[str, Any],
            config: Optional[Any] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """执行单步推理（异步）"""
        try:
            # 1. 解析输入
            user_input = input.get("user_input")

            if not user_input:
                return {
                    "output": "No input provided",
                    "intermediate_steps": [],
                    "success": False,
                    "iterations": 0
                }

            # 构建输入消息
            task_message = f"任务描述: {user_input}\n\n请根据描述完成任务。"

            result = await self.agent_executor.ainvoke({
                "input": task_message,
                "chat_history": self.conversation_history
            })

            # 更新对话历史
            self.conversation_history.append(HumanMessage(content=task_message))
            self.conversation_history.append(AIMessage(content=result["output"]))

            # 提取工具调用信息
            intermediate_steps = result.get("intermediate_steps", [])

            return {
                "output": result["output"],
                "intermediate_steps": intermediate_steps,
                "success": True,
                "iterations": len(intermediate_steps)
            }

        except Exception as e:
            logger.error(
                f"{self.__class__.agent_name} error: {e}",
                exc_info=True
            )
            return {
                "output": f"Error: {str(e)}",
                "intermediate_steps": [],
                "success": False,
                "iterations": 0,
                "error": str(e)
            }

    def invoke(
            self,
            input: Dict[str, Any],
            config: Optional[RunnableConfig] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """同步执行（内部调用 ainvoke）"""
        return asyncio.run(self.ainvoke(input, config, **kwargs))

    @classmethod
    def create_all_agents(
            cls,
            llm: BaseChatModel,
            tool_manager: ToolRegistry,
            check_dependencies: bool = True
    ) -> Dict[str, 'BaseAgent']:
        """
        创建所有注册的 Agent

        自动处理:
        - 平台兼容性
        - 工具依赖检查
        - 优先级排序
        """
        agents = {}

        # 按优先级排序
        sorted_types = sorted(
            cls._registry.keys(),
            key=lambda t: cls._metadata[t].priority,
            reverse=True
        )

        for agent_type in sorted_types:
            agent_class = cls._registry[agent_type]
            metadata = cls._metadata[agent_type]

            # 检查是否启用
            if not metadata.enabled:
                logger.info(f"Skipping {agent_type}: disabled")
                continue

            # 检查工具依赖
            if check_dependencies and metadata.required_tools:
                if not metadata.check_tools_available(tool_manager):
                    logger.warning(
                        f"Skipping {agent_type}: "
                        f"missing tools {metadata.required_tools}"
                    )
                    continue

            # 实例化
            try:
                agent = agent_class(
                    llm=llm,
                    tool_manager=tool_manager
                )
                agents[agent_type] = agent
                logger.info(f"Created: {agent_type}")

            except Exception as e:
                logger.error(
                    f"Failed to create {agent_type}: {e}",
                    exc_info=True
                )

        logger.info(
            f"Successfully loaded {len(agents)}/{len(sorted_types)} agents"
        )
        return agents

    @classmethod
    def get_all_agent_types(cls, sorted_by_priority: bool = True) -> List[str]:
        """获取所有注册的 Agent 类型"""
        agent_types = list(cls._registry.keys())

        if sorted_by_priority:
            agent_types.sort(
                key=lambda t: cls._metadata[t].priority,
                reverse=True
            )

        return agent_types

    @classmethod
    def get_agent_metadata(cls, agent_type: str) -> Optional[AgentMetadata]:
        """获取 Agent 元数据"""
        return cls._metadata.get(agent_type)

    def get_ability_info(self) -> Dict[str, Any]:
        """获取 Agent 能力信息"""
        return {
            "name": self.__class__.agent_name,
            "description": self.__class__.agent_description,
            "tools": [tool.name for tool in self.tools],
            "max_iterations": self.config.max_iterations
        }
