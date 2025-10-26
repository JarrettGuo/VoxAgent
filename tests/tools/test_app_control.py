#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : test_app_control.py
"""

from src.core.tools import app_control


def test_app_control_open():
    tool = app_control()

    # 测试打开应用
    result = tool._run(app_name="记事本", action="open")
    print(result)

    # 测试打开应用
    result = tool._run(app_name="浏览器", action="open")
    print(result)

def test_app_close():
    tool = app_control()

    # 测试关闭应用
    result = tool._run(app_name="记事本", action="close")
    print(result)

    # 测试关闭未打开的应用
    result = tool._run(app_name="记事本", action="close")
    print(result)
