#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : macos_schemas.py
"""

from typing import Optional, Literal

from pydantic import BaseModel, Field


class MailSearchSchema(BaseModel):
    """邮件搜索参数"""
    query: str = Field(description="搜索关键词，可以是发件人、主题或内容")
    mailbox: str = Field(
        default="INBOX",
        description="邮箱名称，默认为收件箱"
    )
    limit: int = Field(
        default=10,
        description="返回的最大邮件数量"
    )


class MailReadSchema(BaseModel):
    """邮件阅读参数"""
    index: int = Field(
        description="邮件索引（从搜索结果中获取）"
    )


class MailSendSchema(BaseModel):
    """邮件发送参数"""
    to_address: str = Field(description="收件人邮箱地址")
    subject: str = Field(description="邮件主题")
    content: str = Field(description="邮件内容")
    cc: Optional[str] = Field(default=None, description="抄送地址（可选）")


class MusicPlaySchema(BaseModel):
    """音乐播放参数"""
    song_name: str = Field(description="歌曲名称")


class MusicControlSchema(BaseModel):
    """音乐控制参数"""
    action: Literal["play", "pause", "next", "previous", "stop"] = Field(
        description="控制操作：play(播放), pause(暂停), next(下一首), previous(上一首), stop(停止)"
    )


class MusicSearchSchema(BaseModel):
    """音乐搜索参数"""
    query: str = Field(description="搜索关键词（歌曲名、歌手或专辑）")
    limit: int = Field(default=5, description="返回结果数量")
