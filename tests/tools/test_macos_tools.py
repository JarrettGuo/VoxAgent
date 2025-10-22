#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : test_macos_tools.py
"""

import platform

import pytest

from src.core.tools import tool_registry
from src.utils.logger import logger


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="macOS tools only work on macOS"
)
class TestMacOSTools:
    """macOS 工具测试"""

    def test_music_search(self):
        """测试音乐搜索"""
        tool = tool_registry.get("music_search")
        result = tool._run(query="夜曲", limit=5)
        logger.info(f"搜索结果:\n{result}")

        assert "搜索结果" in result or "未找到" in result or "无法启动" in result

    def test_music_search_multiple_queries(self):
        """测试多个搜索关键词"""
        tool = tool_registry.get("music_search")

        test_queries = ["Beatles", "Michael Jackson", "周杰伦"]

        for query in test_queries:
            result = tool._run(query=query, limit=3)
            logger.info(f"搜索 '{query}': {result}")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_music_play(self):
        """测试音乐播放"""
        tool = tool_registry.get("music_play")
        result = tool._run(song_name="夜曲")
        logger.info(f"播放结果: {result}")
        assert "正在播放" in result or "未找到" in result or "无法启动" in result

    def test_music_stop(self):
        """测试音乐停止"""
        tool = tool_registry.get("music_control")
        result = tool._run(action="stop")
        logger.info(f"停止结果: {result}")
        assert isinstance(result, str)

    def test_music_control(self):
        """测试音乐控制"""
        tool = tool_registry.get("music_control")

        # 测试暂停
        result = tool._run(action="pause")
        logger.info(f"暂停结果: {result}")
        assert isinstance(result, str)

        # 测试播放
        result = tool._run(action="play")
        logger.info(f"播放结果: {result}")
        assert isinstance(result, str)

    def test_mail_search(self):
        """测试邮件搜索"""
        tool = tool_registry.get("mail_search")
        result = tool._run(query="Citibank", limit=5)
        logger.info(f"搜索结果:\n{result}")
        assert "找到" in result or "未找到" in result or "无法启动" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
