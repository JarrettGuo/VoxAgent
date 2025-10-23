import sys

from src.core.agent.agents.workers.base_worker_agent import BaseWorkerAgent
from src.core.tools import tool_registry
from src.utils.config import config
from langchain_openai import ChatOpenAI

from src.utils.logger import logger


def main():
    logger.info("=" + "=" * 70)
    logger.info(" " * 15 + "TEST AGENT REGISTRY")
    logger.info("=" * 70)
    registry = BaseWorkerAgent.get_registry()
    qiniu_config = config.get("qiniu")
    llm = ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
        temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
        max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
    )
    logger.info(registry)

    all_agents = {name: cls(llm=llm, tool_manager=tool_registry) for name, cls in registry.items()}
    logger.info(f"Initialized agents: {all_agents}")

    logger.info(f"{[ agent.get_ability_info() for agent in all_agents.values()]}")

if __name__ == '__main__':
    sys.exit(main())