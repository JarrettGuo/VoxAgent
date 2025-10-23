#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : test_app_control.py
"""

from src.core.tools import app_control


def test_app_control():
    tool = app_control()

    # 测试打开应用
    result = tool._run(app_name="wechat", action="open")
    print(result)

    # # 测试关闭应用
    # result = tool._run(app_name="chrome", action="close")
    # print(result)
