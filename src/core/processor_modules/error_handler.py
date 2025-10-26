#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : error_handler.py
"""

import re
from difflib import get_close_matches
from enum import Enum
from typing import Dict, Any, Tuple, Optional

from src.utils.logger import logger


class ErrorType(Enum):
    """错误类型枚举"""
    MISSING_INFO = "missing_info"
    RECOGNITION_ERROR = "recognition_error"
    INVALID_PARAM = "invalid_param"
    EXECUTION_FAILED = "execution_failed"
    UNKNOWN = "unknown"


class ErrorHandler:
    """错误处理模块 - 负责错误分析和纠正建议"""

    def __init__(self, error_analyzer):
        self.error_analyzer = error_analyzer

    def analyze_error(
            self,
            execution_result: Dict[str, Any],
            original_query: str
    ) -> Tuple[ErrorType, Dict[str, Any]]:
        """
        分析错误类型和详情

        处理两类错误：
        1. Planner阶段失败（orchestrator_result为None）
        2. Worker阶段失败（orchestrator_result.success为False）
        """
        orchestrator_result = execution_result.get("orchestrator_result")

        # 情况1: Planner阶段失败
        if not orchestrator_result:
            summary = execution_result.get("summary", "")

            # 1.1 识别错误（含义不明、无法理解）
            if self._is_recognition_issue(summary):
                suggestion = self._suggest_from_unclear_query(original_query, summary)

                if suggestion:
                    return ErrorType.RECOGNITION_ERROR, {
                        "message": summary,
                        "description": "语音识别",
                        "suggestion": suggestion,
                        "original_query": original_query
                    }
                else:
                    # 没有建议，也判断为 RECOGNITION_ERROR
                    return ErrorType.RECOGNITION_ERROR, {
                        "message": summary,
                        "description": "语音识别",
                        "original_query": original_query
                    }

            # 1.2 缺失信息
            if any(kw in summary for kw in ["未指定", "请提供", "需要", "缺少", "哪个", "哪里"]):
                return ErrorType.MISSING_INFO, {
                    "message": summary,
                    "description": "任务规划",
                    "original_query": original_query
                }

            # 1.3 不支持的任务
            if any(kw in summary for kw in ["不支持", "无法完成", "超出能力"]):
                # 这种情况应该退出对话，但要友好提示
                return ErrorType.EXECUTION_FAILED, {  # 改为 EXECUTION_FAILED
                    "message": summary,
                    "description": "任务规划"
                }

            # 默认情况下，如果 Planner 说 infeasible，大概率是识别问题，应该允许重试
            return ErrorType.RECOGNITION_ERROR, {  # 改为 RECOGNITION_ERROR
                "message": summary,
                "original_query": original_query
            }

        # 情况2: Worker阶段失败（原有逻辑保持）
        if orchestrator_result:
            results = orchestrator_result.get("results", [])

            for result in results:
                error = result.get("error", "")
                suggestion = result.get("suggestion")
                description = result.get("description", "执行任务")

                # 2.1 文件未找到（特殊处理）
                if "文件不存在" in error or "未找到" in error or "not found" in error.lower():
                    return ErrorType.RECOGNITION_ERROR, {
                        "message": error,
                        "description": description,
                        "suggestion": suggestion,
                        "original_query": original_query
                    }

                # 2.2 缺失参数
                if self.is_missing_param_error(error):
                    return ErrorType.MISSING_INFO, {
                        "message": error,
                        "description": description,
                        "original_query": original_query
                    }

                # 2.3 参数无效
                if self.is_invalid_param_error(error):
                    # 尝试生成建议
                    if not suggestion:
                        suggestion = self.suggest_correction(
                            original_query, error, description
                        )

                    if suggestion:
                        return ErrorType.RECOGNITION_ERROR, {
                            "message": error,
                            "description": description,
                            "suggestion": suggestion,
                            "original_query": original_query
                        }
                    else:
                        return ErrorType.INVALID_PARAM, {
                            "message": error,
                            "description": description
                        }

                # 2.4 权限错误（不可重试）
                if "权限" in error or "permission" in error.lower():
                    return ErrorType.EXECUTION_FAILED, {
                        "message": error,
                        "description": description
                    }

                # 2.5 其他执行错误
                if self.is_execution_error(error):
                    return ErrorType.EXECUTION_FAILED, {
                        "message": error,
                        "description": description
                    }

        return ErrorType.UNKNOWN, {"message": "未知错误"}

    @staticmethod
    def is_missing_param_error(error: str) -> bool:
        """判断是否为缺失参数错误"""
        missing_keywords = [
            "未指定", "缺少", "请提供", "需要",
            "没有提供", "请说明", "必须提供"
        ]
        return any(kw in error for kw in missing_keywords)

    @staticmethod
    def is_invalid_param_error(error: str) -> bool:
        """判断是否为无效参数错误"""
        invalid_keywords = [
            "未找到", "不存在", "无效", "找不到",
            "Don't find", "not found", "invalid",
            "无法识别", "无法查询"
        ]
        return any(kw in error for kw in invalid_keywords)

    @staticmethod
    def is_execution_error(error: str) -> bool:
        """判断是否为执行错误"""
        execution_keywords = [
            "Permission denied", "权限不足",
            "Timeout", "超时", "网络",
            "Connection", "连接失败"
        ]
        return any(kw in error for kw in execution_keywords)

    def suggest_correction(
            self,
            original_query: str,
            error: str,
            description: str
    ) -> Optional[str]:
        """基于错误信息建议可能的正确值"""

        if "天气" in description or "weather" in description.lower():
            return self.extract_possible_city(original_query, error)

        if "文件" in description or "file" in description.lower():
            return self.extract_possible_path(original_query, error)

        return None

    @staticmethod
    def extract_possible_city(query: str, error: str) -> Optional[str]:
        """从查询中提取可能的城市名并纠正"""
        COMMON_CITIES = [
            "北京", "上海", "广州", "深圳", "杭州", "南京",
            "成都", "武汉", "西安", "重庆", "天津", "苏州",
            "波士顿", "纽约", "旧金山", "洛杉矶", "芝加哥",
            "伦敦", "巴黎", "东京", "首尔", "新加坡"
        ]

        words = query.replace("天气", "").replace("查询", "").replace("的", "").split()

        for word in words:
            if len(word) >= 2:
                matches = get_close_matches(word, COMMON_CITIES, n=1, cutoff=0.6)
                if matches:
                    return matches[0]

        # 从错误信息中提取
        match = re.search(r"['\"](.*?)['\"]", error)
        if match:
            wrong_name = match.group(1)
            matches = get_close_matches(wrong_name, COMMON_CITIES, n=1, cutoff=0.5)
            if matches:
                return matches[0]

        return None

    @staticmethod
    def extract_possible_path(query: str, error: str) -> Optional[str]:
        """从查询中提取可能的文件路径"""
        COMMON_LOCATIONS = {
            "桌面": "~/Desktop",
            "文档": "~/Documents",
            "下载": "~/Downloads",
            "图片": "~/Pictures",
        }

        for location, path in COMMON_LOCATIONS.items():
            if location in query:
                return path

        return None

    def generate_clarification_question(
            self,
            execution_result: Dict[str, Any],
            original_query: str,
            conversation_messages: list
    ) -> str:
        """生成友好的错误提示"""

        error_type, error_details = self.analyze_error(execution_result, original_query)

        error_message = error_details.get("message", "未知错误")
        task_description = error_details.get("description", "执行任务")
        suggestion = error_details.get("suggestion")

        try:
            if self.error_analyzer:
                friendly_message = self.error_analyzer.analyze_error_with_history_sync(
                    conversation_history=conversation_messages,
                    original_query=original_query,
                    task_description=task_description,
                    error_message=error_message,
                    error_type=error_type.value,
                    suggestion=suggestion
                )
                return friendly_message
            else:
                logger.warning("ErrorAnalyzerAgent not initialized")
                return self.generate_fallback_question(error_type, error_details)
        except Exception as e:
            logger.error(f"Error analysis failed: {e}", exc_info=True)
            return self.generate_fallback_question(error_type, error_details)

    @staticmethod
    def generate_fallback_question(error_type: ErrorType, error_details: Dict) -> str:
        """降级方案：简单提示生成"""
        message = error_details.get("message", "")

        if error_type == ErrorType.MISSING_INFO:
            if "城市" in message or "地点" in message:
                return "请问要查询哪个城市的天气？"
            if "文件" in message and "路径" in message:
                return "请问要在哪里创建文件？比如桌面、文档或下载文件夹。"
            return f"{message}请补充说明。"

        elif error_type == ErrorType.RECOGNITION_ERROR:
            suggestion = error_details.get("suggestion")
            original = error_details.get("original_query", "")
            if suggestion:
                return f"我听到的是'{original}'，您是想说'{suggestion}'吗？如果是，请说'是'；如果不是，请重新说明。"

        elif error_type == ErrorType.INVALID_PARAM:
            return f"{message}。请重新说明或提供正确的信息。"

        elif error_type == ErrorType.EXECUTION_FAILED:
            if "Permission denied" in message or "权限" in message:
                return "没有权限执行此操作。请尝试其他位置或检查权限设置。"
            if "Timeout" in message or "超时" in message:
                return "操作超时，可能是网络问题。请稍后重试。"
            return f"执行失败：{message}。请重试或更换其他方式。"

        return "抱歉，遇到了一些问题。请重新描述您的需求。"

    def _is_recognition_issue(self, text: str) -> bool:
        """判断是否为语音识别问题"""
        recognition_keywords = [
            "含义不明", "无法理解", "不明确",
            "无法识别", "无法确定", "不清楚",
            "无法查询"
        ]
        return any(kw in text for kw in recognition_keywords)

    def _suggest_from_unclear_query(
            self,
            original_query: str,
            error_message: str
    ) -> Optional[str]:
        """
        从不明确的查询中提取可能的纠正

        策略：
        1. 提取错误信息中标注的"不明词汇"（通常在引号中）
        2. 对这些词汇进行智能匹配
        3. 结合上下文（如"天际"可能是"天气"）
        """
        import re

        # 提取引号中的不明词汇
        unclear_words = re.findall(r'["""\'](.*?)["""\']', error_message)

        logger.debug(f"Extracted unclear words: {unclear_words}")

        for word in unclear_words:
            # 策略1: 天气查询纠正
            if "天际" in word or "天气" in word:
                # "天际"很可能是"天气"的误识
                corrected_query = original_query.replace("天际", "天气")

                # 尝试提取城市名
                potential_city = self.extract_possible_city(corrected_query, error_message)
                if potential_city:
                    return f"查询{potential_city}天气"

            # 策略2: 城市名纠正
            # "薄时盾" → "波士顿"
            city_suggestion = self.extract_possible_city(original_query, word)
            if city_suggestion:
                # 构建完整查询
                if "天际" in original_query or "天气" in original_query:
                    return f"查询{city_suggestion}天气"
                return city_suggestion

        return None
