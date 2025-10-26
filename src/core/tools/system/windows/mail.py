from typing import Optional, Any, Type

from src.core.tools.base import OutlookSendSchema, OutlookSearchSchema, OutlookReadSchema
from src.core.tools.system.windows.base import WindowsBaseTool

from src.utils.logger import logger

import win32com.client
import pythoncom

class OutlookSearchTool(WindowsBaseTool):
    """Outlook搜索工具"""

    name: str = "outlook_search"
    description: str = (
        "在 Microsoft Outlook 应用中搜索邮件。"
        "可以根据发件人、主题或内容进行搜索，返回匹配的邮件列表。"
    )
    args_schema: Type[OutlookSearchSchema] = OutlookSearchSchema

    def _run(
            self,
            query: str,
            folder: str = "Inbox",
            limit: int = 10,
            **kwargs: Any
    ) -> str:
        """执行邮件搜索"""
        try:
            if not self._is_windows() or win32com is None:
                return "This tool only works on Windows with pywin32 installed"

            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")

            # Get the specified folder
            inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            if folder.lower() != "inbox":
                try:
                    target_folder = inbox.Folders[folder]
                except:
                    target_folder = inbox
            else:
                target_folder = inbox

            messages = target_folder.Items
            messages.Sort("[ReceivedTime]", True)  # Sort by received time, descending

            result_list = []
            match_count = 0

            for message in messages:
                if match_count >= limit:
                    break

                try:
                    subject = message.Subject or ""
                    sender = message.SenderName or ""
                    body = message.Body or ""

                    # Check if matches query
                    if (query.lower() in subject.lower() or
                            query.lower() in sender.lower() or
                            query.lower() in body.lower()):
                        received_time = message.ReceivedTime.strftime("%Y-%m-%d %H:%M:%S")
                        unread_status = "未读" if message.UnRead else "已读"

                        msg_info = (
                            f"发件人: {sender}\n"
                            f"主题: {subject}\n"
                            f"日期: {received_time}\n"
                            f"状态: {unread_status}\n"
                            f"---"
                        )

                        result_list.append(msg_info)
                        match_count += 1
                except:
                    continue

            if match_count == 0:
                return "未找到匹配的邮件"
            else:
                return f"找到 {match_count} 封邮件:\n\n" + "\n".join(result_list)

        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            return self._format_error_response(e)
        finally:
            pythoncom.CoUninitialize()


class OutlookReadTool(WindowsBaseTool):
    """Outlook阅读工具"""

    name: str = "outlook_read"
    description: str = "读取指定索引的邮件完整内容"
    args_schema: Type[OutlookReadSchema] = OutlookReadSchema

    def _run(self, index: int, folder: str = "Inbox", **kwargs: Any) -> str:
        """读取邮件内容"""
        try:
            if not self._is_windows() or win32com is None:
                return "This tool only works on Windows with pywin32 installed"

            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")

            inbox = namespace.GetDefaultFolder(6)
            if folder.lower() != "inbox":
                try:
                    target_folder = inbox.Folders[folder]
                except:
                    target_folder = inbox
            else:
                target_folder = inbox

            messages = target_folder.Items
            messages.Sort("[ReceivedTime]", True)

            if index < 1 or index > messages.Count:
                return f"Invalid index. Folder contains {messages.Count} emails."

            message = messages[index]

            sender = message.SenderName or "Unknown"
            subject = message.Subject or "No Subject"
            received_time = message.ReceivedTime.strftime("%Y-%m-%d %H:%M:%S")
            body = message.Body or "No content"

            result = (
                f"发件人: {sender}\n"
                f"主题: {subject}\n"
                f"日期: {received_time}\n\n"
                f"内容:\n{body}"
            )
            return result

        except Exception as e:
            logger.error(f"Error reading email: {str(e)}")
            return self._format_error_response(e)
        finally:
            pythoncom.CoUninitialize()


class OutlookSendTool(WindowsBaseTool):
    """邮件发送工具"""

    name: str = "outlook_send"
    description: str = "通过 Microsoft Outlook 发送邮件"
    args_schema: Type[OutlookSendSchema] = OutlookSendSchema

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
            if not self._is_windows() or win32com is None:
                return "This tool only works on Windows with pywin32 installed"

            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")

            mail = outlook.CreateItem(0)  # 0 = olMailItem
            mail.To = to_address
            mail.Subject = subject
            mail.Body = content

            if cc:
                mail.CC = cc

            mail.Send()

            pythoncom.CoUninitialize()

            logger.info(f"Sent email to: {to_address}")
            return f"邮件已发送到: {to_address}"

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return self._format_error_response(e)
        finally:
            pythoncom.CoUninitialize()

def outlook_search(**kwargs) -> WindowsBaseTool:
    """工厂函数：创建邮件搜索工具"""
    return OutlookSearchTool(**kwargs)


def outlook_read(**kwargs) -> WindowsBaseTool:
    """工厂函数：创建邮件阅读工具"""
    return OutlookReadTool(**kwargs)


def outlook_send(**kwargs) -> WindowsBaseTool:
    """工厂函数：创建邮件发送工具"""
    return OutlookSendTool(**kwargs)