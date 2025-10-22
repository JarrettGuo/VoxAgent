#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : wikipedia.py
"""

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import WikipediaSearchSchema
from src.utils.logger import logger


def wikipedia_search(**kwargs) -> BaseTool:
    """维基百科搜索工具"""
    try:

        # 创建 API 包装器（可以配置语言等参数）
        api_wrapper = WikipediaAPIWrapper(
            top_k_results=2,  # 返回前2个结果
            doc_content_chars_max=4000,  # 每个文档最多4000字符
            lang="zh",  # 中文维基百科
        )

        tool = WikipediaQueryRun(
            name="wikipedia_search",
            description=(
                "维基百科搜索工具。当你需要查询百科知识、概念定义、"
                "历史事件、人物信息等内容时可以使用。工具的输入是一个查询关键词。"
            ),
            api_wrapper=api_wrapper,
            args_schema=WikipediaSearchSchema,
            **kwargs
        )

        logger.info("维基百科搜索工具创建成功")
        return tool

    except Exception as e:
        logger.error(f"创建维基百科搜索工具失败: {e}")
        raise
