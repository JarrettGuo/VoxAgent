#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : mail.py
"""
from typing import Any, Type, Optional

from src.core.tools.base import MailSearchSchema, MailSendSchema, MailReadSchema
from src.core.tools.system.macos.base import MacOSBaseTool, AppleScriptError
from src.utils.logger import logger


class MailSearchTool(MacOSBaseTool):
    """邮件搜索工具"""

    name: str = "mail_search"
    description: str = (
        "在 macOS Mail 应用中搜索邮件。"
        "可以根据发件人、主题或内容进行搜索，返回匹配的邮件列表。"
    )
    args_schema: Type[MailSearchSchema] = MailSearchSchema

    def _run(
            self,
            query: str,
            mailbox: str = "INBOX",
            limit: int = 10,
            **kwargs: Any
    ) -> str:
        """执行邮件搜索"""
        try:
            # 确保 Mail 应用正在运行
            if not self._ensure_app_running("Mail"):
                return "无法启动 Mail 应用"

            #  AppleScript
            script = f'''
            tell application "Mail"
                set resultList to {{}}
                set matchCount to 0

                try
                    -- 获取收件箱（支持多账户）
                    set allAccounts to every account
                    set allMessages to {{}}

                    repeat with acc in allAccounts
                        try
                            set inboxRef to mailbox "INBOX" of acc
                            set accMessages to messages of inboxRef
                            set allMessages to allMessages & accMessages
                        end try
                    end repeat

                    if (count of allMessages) = 0 then
                        return "邮箱中没有邮件"
                    end if

                    -- 搜索邮件
                    repeat with msg in allMessages
                        if matchCount >= {limit} then exit repeat

                        try
                            set msgSubject to subject of msg
                            set msgSender to sender of msg

                            -- 检查是否匹配查询
                            if msgSubject contains "{query}" or msgSender contains "{query}" then
                                set msgDate to date received of msg
                                set msgRead to read status of msg

                                set readStatus to "未读"
                                if msgRead then
                                    set readStatus to "已读"
                                end if

                                set msgInfo to "发件人: " & msgSender & linefeed & ¬
                                             "主题: " & msgSubject & linefeed & ¬
                                             "日期: " & (msgDate as string) & linefeed & ¬
                                             "状态: " & readStatus & linefeed & "---"

                                set end of resultList to msgInfo
                                set matchCount to matchCount + 1
                            end if
                        end try
                    end repeat

                    if matchCount = 0 then
                        return "未找到匹配的邮件"
                    else
                        set AppleScript's text item delimiters to linefeed
                        set resultText to resultList as text
                        set AppleScript's text item delimiters to ""
                        return "找到 " & (matchCount as string) & " 封邮件:" & linefeed & linefeed & resultText
                    end if

                on error errMsg
                    return "搜索邮件时出错: " & errMsg
                end try
            end tell
            '''

            result = self._execute_applescript(script)
            logger.info(f"搜索到邮件: {query}")

            return result

        except AppleScriptError as e:
            return self._format_error_response(e)


class MailReadTool(MacOSBaseTool):
    """邮件阅读工具"""

    name: str = "mail_read"
    description: str = "读取指定索引的邮件完整内容"
    args_schema: Type[MailReadSchema] = MailReadSchema

    def _run(self, index: int, **kwargs: Any) -> str:
        """读取邮件内容"""
        try:
            if not self._ensure_app_running("Mail"):
                return "无法启动 Mail 应用"

            script = f'''
            tell application "Mail"
                set msg to message {index} of inbox

                set msgSender to sender of msg
                set msgSubject to subject of msg
                set msgDate to date received of msg
                set msgContent to content of msg

                return "发件人: " & msgSender & "\\n" & ¬
                       "主题: " & msgSubject & "\\n" & ¬
                       "日期: " & (msgDate as string) & "\\n\\n" & ¬
                       "内容:\\n" & msgContent
            end tell
            '''

            result = self._execute_applescript(script)
            return result

        except AppleScriptError as e:
            return self._format_error_response(e)


class MailSendTool(MacOSBaseTool):
    """邮件发送工具"""

    name: str = "mail_send"
    description: str = "通过 macOS Mail 发送邮件"
    args_schema: Type[MailSendSchema] = MailSendSchema

    def _run(
            self,
            to_address: str,
            subject: str,
            content: str,
            cc: Optional[str] = None,
            **kwargs: Any
    ) -> str:
        """发送邮件"""
        try:
            if not self._ensure_app_running("Mail"):
                return "Cannot start Mail application"

            # 构建抄送部分
            cc_script = ""
            if cc:
                cc_script = f'set cc recipients to "{cc}"'

            script = f'''
            tell application "Mail"
                set newMessage to make new outgoing message with properties {{¬
                    subject:"{subject}", ¬
                    content:"{content}", ¬
                    visible:true}}

                tell newMessage
                    make new to recipient at end of to recipients ¬
                        with properties {{address:"{to_address}"}}
                    {cc_script}
                end tell

                -- 发送邮件
                send newMessage

                return "邮件已发送到: {to_address}"
            end tell
            '''

            result = self._execute_applescript(script)
            logger.info(f"Sent email to: {to_address}")

            return result

        except AppleScriptError as e:
            return self._format_error_response(e)


def mail_search(**kwargs) -> MacOSBaseTool:
    """工厂函数：创建邮件搜索工具"""
    return MailSearchTool(**kwargs)


def mail_read(**kwargs) -> MacOSBaseTool:
    """工厂函数：创建邮件阅读工具"""
    return MailReadTool(**kwargs)


def mail_send(**kwargs) -> MacOSBaseTool:
    """工厂函数：创建邮件发送工具"""
    return MailSendTool(**kwargs)
