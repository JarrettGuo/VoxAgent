#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : duckduckgo.py
"""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import DuckDuckGoSearchSchema
from src.utils.logger import logger


def duckduckgo_search(**kwargs) -> BaseTool:
    """工厂函数：创建 DuckDuckGo 搜索工具"""
    try:
        logger.info("创建 DuckDuckGo 搜索工具")

        tool = DuckDuckGoSearchRun(
            name="duckduckgo_search",
            description=(
                "一个注重隐私的搜索引擎。当你需要搜索实时信息、新闻、网页等内容并且注重隐私时，可以使用此工具。工具的输入是一个查询语句。"
            ),
            args_schema=DuckDuckGoSearchSchema,
            **kwargs
        )

        logger.info("DuckDuckGo 搜索工具创建成功")
        return tool

    except Exception as e:
        logger.error(f"创建 DuckDuckGo 搜索工具失败: {e}")
        raise
