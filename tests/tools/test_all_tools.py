#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : test_all_tools.py
"""

from src.core.tools import tool_registry
from src.utils.logger import logger


# tests/tools/test_all_tools.py
def test_all_tools():
    """测试所有已注册的工具"""
    # 显示所有已注册的工具
    tool_names = tool_registry.get_tool_names()
    logger.info(f"\n已注册工具 ({len(tool_names)} 个):")
    for name in tool_names:
        logger.info(f"   - {name}")

    # 测试 DuckDuckGo 搜索
    logger.info("\n测试 DuckDuckGo 搜索")
    try:
        tool = tool_registry.get("duckduckgo_search")
        result = tool._run(query="Python programming")
        logger.info(f"Result: {result[:200]}...")
    except ValueError as e:
        # 如果工具未注册，尝试手动创建看看真正的错误
        logger.error(f"工具未注册: {e}")
        logger.info("尝试手动创建工具查看错误...")
        try:
            from src.core.tools.search import duckduckgo_search
            tool = duckduckgo_search()
            logger.info("手动创建成功！")
        except Exception as create_error:
            logger.error(f"创建失败的真正原因: {create_error}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 类似地测试高德天气
    logger.info("\n" + "=" * 60)
    logger.info("测试高德天气")
    logger.info("=" * 60)
    try:
        tool = tool_registry.get("gaode_weather")
        result = tool._run(city="北京")
        logger.info(f"结果:\n{result}")
    except ValueError as e:
        logger.error(f"工具未注册: {e}")
        logger.info("尝试手动创建工具查看错误...")
        try:
            from src.core.tools.weather import gaode_weather
            tool = gaode_weather()
            logger.info("手动创建成功！")
        except Exception as create_error:
            logger.error(f"创建失败的真正原因: {create_error}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    logger.info("\n测试完成!")


if __name__ == "__main__":
    test_all_tools()
