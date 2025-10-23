import platform
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, Optional, List

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langchain_core.language_models import BaseChatModel

from src.core.agent.entities.agent_entity import AgentMetadata
from src.core.tools import ToolRegistry, tool_registry
from src.utils.config import config
from src.utils.logger import logger


class BaseWorkerAgent(Runnable, ABC):

    _registry: Dict[str, Type['BaseWorkerAgent']] = {}
    _metadata: Dict[str, AgentMetadata] = {}

    def __init_subclass__(
            cls,
            agent_type: str = None,
            priority: int = 50,
            platforms: Optional[List[str]] = None,
            required_tools: Optional[List[str]] = None,
            enabled: bool = True,
            **kwargs
    ):
        """
        当子类被定义时自动调用

        参数:
            agent_type: Agent类型标识符
            priority: 优先级 (0-100, 数字越大优先级越高)
            platforms: 支持的平台列表 ["macos", "linux", "windows"]
            required_tools: 必需的工具列表
            enabled: 是否启用该agent

        用法:
            class FileAgent(BaseAgent, agent_type="file", priority=80):
                ...

            class MacOSAgent(BaseAgent, agent_type="macos", platforms=["macos"]):
                ...
        """
        super().__init_subclass__(**kwargs)
        if agent_type:
            # 创建元数据
            metadata = AgentMetadata(
                agent_type=agent_type,
                priority=priority,
                platforms=platforms,
                required_tools=required_tools,
                enabled=enabled
            )

            # 检查平台兼容性
            if not metadata.is_platform_compatible():
                logger.info(
                    f"⏭️  Skipping {cls.__name__}: not compatible with {platform.system()}"
                )
                return

            # 注册agent
            cls._registry[agent_type] = cls
            cls._metadata[agent_type] = metadata

            logger.info(
                f"✅ Registered: {agent_type} -> {cls.__name__} "
                f"(priority={priority}, platforms={platforms or 'all'})"
            )

    def __init__(
         self,
         name: str,
         description: str,
         llm: BaseChatModel,
         tools: List[str],
         tool_manager: ToolRegistry,
         **kwargs
    ):
        self.name = name
        self.description = description
        self.tool_names = tools
        self.tool_manager = tool_manager
        self.llm = llm

    @classmethod
    def get_registry(cls):
        return cls._registry

    # @abstractmethod
    # def _build_agent(self) -> CompiledStateGraph:
    #     """构建 LangGraph 图结构（子类必须实现）"""
    #     raise NotImplementedError("Subclass must implement _build_agent()")
    @abstractmethod
    def run(self, task: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    def invoke(self, input_data: Input, config: RunnableConfig | None = None, **kwargs: Any) -> Output:
        self.run(input_data)

    @classmethod
    def get_agent_metadata(cls, agent_type: str) -> Optional[AgentMetadata]:
        """获取Agent的元数据"""
        return cls._metadata.get(agent_type)

    def get_ability_info(self):
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tool_names,
        }

    @classmethod
    def get_all_agent_types(cls, sorted_by_priority: bool = True) -> List[str]:
        """
        获取所有已注册的Agent类型

        参数:
            sorted_by_priority: 是否按优先级排序
        """
        agent_types = list(cls._registry.keys())

        if sorted_by_priority:
            agent_types.sort(
                key=lambda t: cls._metadata[t].priority,
                reverse=True  # 高优先级在前
            )
        return agent_types

    @classmethod
    def create_all_agents(
        cls,
        llm: BaseChatModel,
        tool_manager: ToolRegistry,
        check_dependencies: bool = True
    ) -> Dict[str, 'BaseWorkerAgent']:
        """
        实例化所有已注册的Agent

        参数:
            tool_manager: 工具管理器
            check_dependencies: 是否检查工具依赖

        返回:
            成功创建的agents字典
        """
        agents = {}

        # 按优先级排序
        sorted_types = cls.get_all_agent_types(sorted_by_priority=True)

        for agent_type in sorted_types:
            agent_class = cls._registry[agent_type]
            metadata = cls._metadata[agent_type]

            # 检查是否启用
            if not metadata.enabled:
                logger.info(f"⏭️  Skipping {agent_type}: disabled")
                continue

            # 检查工具依赖
            if check_dependencies and not metadata.check_tools_available(tool_manager):
                logger.warning(
                    f"⚠️  Skipping {agent_type}: missing required tools "
                    f"{metadata.required_tools}"
                )
                continue

            # 实例化agent
            try:
                agents[agent_type] = agent_class(tool_manager=tool_manager, llm=llm)
                logger.info(
                    f"✅ Created agent: {agent_type} "
                    f"(priority={metadata.priority})"
                )
            except Exception as e:
                logger.error(f"❌ Failed to create {agent_type}: {e}")

        logger.info(
            f"🎉 Successfully loaded {len(agents)}/{len(sorted_types)} agents"
        )
        return agents
