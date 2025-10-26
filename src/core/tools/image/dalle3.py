#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : dalle3.py
"""

from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import SecretStr

from src.core.tools.base.schemas import Dalle3Schema
from src.utils.logger import logger


def dalle3(api_key: SecretStr = None, **kwargs) -> BaseTool:
    """DALL·E 3 图像生成工具"""
    try:
        if api_key is None:
           raise Exception("api_key not passed.")
        # 创建 API 包装器
        api_wrapper = DallEAPIWrapper(
            model="dall-e-3",
            api_key=api_key,
            **kwargs
        )

        tool = OpenAIDALLEImageGenerationTool(
            name="dalle3",
            description=(
                "DALL·E 3 图像生成工具。根据文本描述生成高质量图像。"
                "输入详细的图像描述（建议使用英文），返回生成的图像 URL。"
            ),
            api_wrapper=api_wrapper,
            args_schema=Dalle3Schema,
        )

        logger.info("DALL·E 3 图像生成工具创建成功")
        return tool

    except Exception as e:
        logger.error(f"创建 DALL·E 3 图像生成工具失败: {e}")
        raise
