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
    """应用控制参数"""
    app_name: str = Field(description="应用程序名称，例如：Chrome、微信、记事本、Apple Music等")
    action: Literal["open", "close"] = Field(description="操作类型：open(打开) 或 close(关闭)")


class DuckDuckGoSearchSchema(BaseModel):
    """DuckDuckGo 搜索参数"""
    query: str = Field(description="需要检索查询的语句")


class GoogleSerperSchema(BaseModel):
    """Google Serper 搜索参数"""
    query: str = Field(description="需要检索查询的语句，例如：'2024年人工智能发展趋势'")


class WikipediaSearchSchema(BaseModel):
    """维基百科搜索参数"""
    query: str = Field(description="需要在维基百科中查询的关键词")


class GaodeWeatherSchema(BaseModel):
    """高德天气查询参数"""
    city: str = Field(description="需要查询天气预报的目标城市，例如：北京、上海、广州等")


class Dalle3Schema(BaseModel):
    """DALL·E 3 图像生成参数"""
    query: str = Field(description="用于生成图像的文本提示（英文效果更好）")
