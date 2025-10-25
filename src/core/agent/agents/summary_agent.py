#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : summary_agent.py
"""

from typing import Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.utils.logger import logger


class SummaryAgent:
    """
    结果总结 Agent - 将执行结果转换为用户友好的自然语言
    """

    SYSTEM_PROMPT = """你是一个专业的任务执行结果总结专家。

**你的职责：**
将多个任务步骤的执行结果总结成简洁、友好的自然语言，适合语音播报。

**总结原则：**
1. **简洁明了**：避免冗余信息，直击要点
2. **用户视角**：使用"我"、"已"等第一人称，增强亲切感
3. **结果导向**：重点说明完成了什么，而非过程细节
4. **语音友好**：使用口语化表达，适合TTS播报
5. **状态明确**：清楚说明成功/失败情况

**输出格式要求：**
- 成功任务：直接说明完成了什么
- 失败任务：简要说明原因和建议
- 混合情况：先说成功部分，再提示失败部分

**示例输入：**
```json
{
  "original_query": "搜索Python教程并创建笔记",
  "total_steps": 2,
  "successful_steps": 2,
  "results": [
    {
      "description": "搜索Python教程",
      "output": "Python是一种...(500字)",
      "status": "success"
    },
    {
      "description": "创建笔记文件 ~/Desktop/notes.txt",
      "output": "File created: ~/Desktop/notes.txt",
      "status": "success"
    }
  ]
}
```

**示例输出（成功）：**
"好的，我已经为你搜索了Python教程的相关信息，并在桌面创建了笔记文件notes.txt。你可以打开查看详细内容。"

**示例输出（部分失败）：**
"我已经搜索到了Python教程的信息，但创建笔记文件时遇到权限问题。建议你手动创建文件或选择其他位置。"

**注意：**
- 不要重复输入的详细内容
- 不要使用技术术语（如"执行成功"、"返回结果"等）
- 控制在2-3句话以内
- 适合TTS语音播报
"""

    def __init__(self, llm: BaseChatModel):
        """
        初始化总结 Agent

        Args:
            llm: 语言模型实例
        """
        self.llm = llm
        logger.info("SummarizerAgent initialized")

    async def summarize(
            self,
            original_query: str,
            execution_summary: Dict[str, Any]
    ) -> str:
        """
        异步总结执行结果

        Args:
            original_query: 用户原始问题
            execution_summary: TaskOrchestrator 返回的执行摘要

        Returns:
            用户友好的总结文本
        """
        try:
            # 构建输入
            input_data = self._format_input(original_query, execution_summary)

            # 调用 LLM
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=input_data)
            ]

            response = await self.llm.ainvoke(messages)
            summary = response.content.strip()

            logger.info(f"Generated summary: {summary[:100]}...")
            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            # 降级方案：返回简单的状态描述
            return self._create_fallback_summary(execution_summary)

    def summarize_sync(
            self,
            original_query: str,
            execution_summary: Dict[str, Any]
    ) -> str:
        """
        同步总结执行结果

        Args:
            original_query: 用户原始问题
            execution_summary: TaskOrchestrator 返回的执行摘要

        Returns:
            用户友好的总结文本
        """
        import asyncio
        return asyncio.run(self.summarize(original_query, execution_summary))

    def _format_input(
            self,
            original_query: str,
            execution_summary: Dict[str, Any]
    ) -> str:
        """格式化输入给 LLM"""
        # 提取关键信息
        total_steps = execution_summary.get("total_steps", 0)
        successful_steps = execution_summary.get("successful_steps", 0)
        failed_steps = execution_summary.get("failed_steps", 0)
        results = execution_summary.get("results", [])

        # 构建简洁的结果描述
        results_summary = []
        for idx, result in enumerate(results, 1):
            status = result.get("status", "unknown")
            description = result.get("description", "")
            output = result.get("output", "")

            # 截断过长的输出
            if len(output) > 200:
                output = output[:200] + "..."

            results_summary.append({
                "step": idx,
                "description": description,
                "status": status,
                "output": output
            })

        # 构建提示
        prompt = f"""请总结以下任务执行结果：

**用户原始问题：**
{original_query}

**执行统计：**
- 总步骤数：{total_steps}
- 成功步骤：{successful_steps}
- 失败步骤：{failed_steps}

**步骤详情：**
"""
        for item in results_summary:
            prompt += f"\n步骤 {item['step']}：{item['description']}\n"
            prompt += f"状态：{item['status']}\n"
            if item['output']:
                prompt += f"结果：{item['output']}\n"

        prompt += "\n请生成简洁、自然的语音播报文本（2-3句话）："

        return prompt

    def _create_fallback_summary(self, execution_summary: Dict[str, Any]) -> str:
        """降级方案：生成简单的总结"""
        success = execution_summary.get("success", False)
        total_steps = execution_summary.get("total_steps", 0)
        successful_steps = execution_summary.get("successful_steps", 0)

        if success:
            return f"好的，我已经完成了所有{total_steps}个任务步骤。"
        elif successful_steps == 0:
            return "抱歉，任务执行失败了，请稍后重试。"
        else:
            return f"我已经完成了{successful_steps}个步骤，但还有{total_steps - successful_steps}个步骤未能完成。"
