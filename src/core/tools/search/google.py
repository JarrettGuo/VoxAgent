#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : google.py
"""

from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import GoogleSerperSchema
from src.utils.logger import logger


def google_serper(api_key: str = None, **kwargs) -> BaseTool:
    """
    Google Serper 搜索工具

    Args:
        api_key: Google Serper API Key (如果不提供，会从环境变量读取)
        **kwargs: 其他参数

    Returns:
        BaseTool: Google Serper 搜索工具实例
    """
    try:
        logger.info("创建 Google Serper 搜索工具")

        # 创建 API 包装器
        api_wrapper_kwargs = {}
        if api_key:
            api_wrapper_kwargs['serper_api_key'] = api_key

        api_wrapper = GoogleSerperAPIWrapper(**api_wrapper_kwargs)

        tool = GoogleSerperRun(
            name="google_serper",
            description=(
                "Google搜索工具，用于搜索实时信息、新闻、网页内容等。"
                "当你需要获取最新资讯、查找网页信息、了解时事新闻时使用此工具。"
                "输入应该是一个搜索查询语句。"
            ),
            api_wrapper=api_wrapper,
            args_schema=GoogleSerperSchema,
            **kwargs
        )

        logger.info("Google Serper 搜索工具创建成功")
        return tool

    except Exception as e:
        logger.error(f"创建 Google Serper 搜索工具失败: {e}")
        raise
