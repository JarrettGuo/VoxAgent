#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : schemas.py
"""
from typing import Literal

from pydantic import BaseModel, Field


class AppControlSchema(BaseModel):
    """应用程序控制参数"""
    app_name: str = Field(description="应用程序名称，例如：Chrome、微信、记事本、Apple Music等")
    action: Literal["open", "close"] = Field(description="操作类型：open(打开) 或 close(关闭)")


class FileCreateSchema(BaseModel):
    """文件创建参数"""
    file_path: str = Field(description="要创建的文件路径，例如：/Users/xxx/document.txt")
    content: str = Field(default="", description="文件初始内容（可选）")


class BrowserSearchSchema(BaseModel):
    """浏览器搜索参数"""
    query: str = Field(description="搜索关键词")
    browser: str = Field(default="chrome", description="浏览器名称，默认为 chrome")
