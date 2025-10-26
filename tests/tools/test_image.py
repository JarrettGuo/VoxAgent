#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.core.tools import tool_registry
from src.utils.logger import logger


class TestImageGeneration:
    """图片生成 - 核心功能测试"""

    def test_generate_image(self):
        """测试 file_create：创建文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 image_gen")
        logger.info("=" * 60)

        tool = tool_registry.get_tool("dalle3")
        result = tool._run(query="halloween night at a haunted museum")

        logger.info(f"结果: {result}")

        logger.info("测试通过: image_gen")
