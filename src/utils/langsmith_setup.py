#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : langsmith_setup.py
"""

import os

from src.utils.config import config
from src.utils.logger import logger


class LangSmithManager:
    """LangSmith 监控管理器"""

    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """初始化 LangSmith 环境变量"""
        if cls._initialized:
            logger.warning("LangSmith already initialized")
            return True

        try:
            # 检查是否启用
            enabled = config.get("langsmith.enabled", False)
            if not enabled:
                logger.info("LangSmith tracing is disabled")
                return False

            # 获取配置
            tracing = config.get("langsmith.tracing", True)
            endpoint = config.get("langsmith.endpoint", "https://api.smith.langchain.com")
            api_key = config.get("langsmith.api_key")
            project = config.get("langsmith.project", "voxagent-default")

            # 验证API Key
            if not api_key:
                logger.warning("LangSmith API key not configured, tracing disabled")
                return False

            # 设置环境变量
            os.environ["LANGSMITH_TRACING"] = "true" if tracing else "false"
            os.environ["LANGSMITH_ENDPOINT"] = endpoint
            os.environ["LANGSMITH_API_KEY"] = api_key
            os.environ["LANGSMITH_PROJECT"] = project

            cls._initialized = True

            logger.info("LangSmith initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {e}")
            return False


# 全局初始化函数
def setup_langsmith() -> bool:
    """设置 LangSmith (便捷函数)"""
    return LangSmithManager.initialize()
