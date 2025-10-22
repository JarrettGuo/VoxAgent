#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : agent_queue_manager.py
"""

import time
import uuid
from queue import Queue, Empty
from typing import Generator, Dict
from uuid import UUID

from src.core.agent.entities.queue_entity import AgentThought, QueueEvent
from src.utils.logger import logger


class AgentQueueManager:
    """
    Agent 队列管理器（简化版）

    核心功能：
    1. 管理任务队列（内存队列）
    2. 发布事件到队列
    3. 监听队列并生成事件流
    """

    def __init__(self):
        """初始化队列管理器"""
        self._queues: Dict[str, Queue] = {}  # 任务ID -> 队列的映射
        logger.info("✅ AgentQueueManager initialized")

    def queue(self, task_id: UUID) -> Queue:
        """获取或创建任务队列"""
        task_id_str = str(task_id)

        # 如果队列不存在，创建新队列
        if task_id_str not in self._queues:
            self._queues[task_id_str] = Queue()
            logger.debug(f"📦 Created queue for task: {task_id_str[:8]}...")

        return self._queues[task_id_str]

    def publish(self, task_id: UUID, agent_thought: AgentThought) -> None:
        """发布事件到队列，并记录日志"""
        # 1. 将事件放入队列
        self.queue(task_id).put(agent_thought)

        # 2. 记录日志
        event_type = agent_thought.event.value if hasattr(agent_thought.event, 'value') else agent_thought.event
        logger.debug(f"📤 Published event: {event_type} for task {str(task_id)[:8]}...")

        # 3. 如果是终止事件，停止监听
        if agent_thought.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.AGENT_END]:
            self.stop_listen(task_id)
            logger.debug(f"🛑 Stopped listening for task {str(task_id)[:8]}...")

    def publish_error(self, task_id: UUID, error: Exception) -> None:
        """发布错误事件到队列"""
        self.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.ERROR,
            observation=str(error),
        ))
        logger.error(f"❌ Published error for task {str(task_id)[:8]}...: {str(error)}")

    def listen(self, task_id: UUID, timeout: float = 1.0) -> Generator[AgentThought, None, None]:
        """监听队列并生成事件流（生成器）"""
        logger.info(f"👂 Started listening for task {str(task_id)[:8]}...")
        start_time = time.time()

        while True:
            try:
                # 尝试从队列获取事件（带超时）
                item = self.queue(task_id).get(timeout=timeout)

                # None 是停止信号
                if item is None:
                    logger.info(f"🏁 Received stop signal for task {str(task_id)[:8]}...")
                    break

                # 生成事件
                yield item

            except Empty:
                # 队列为空，继续等待
                continue

            except Exception as e:
                # 发生异常，发布错误事件并停止
                logger.error(f"❌ Error while listening: {e}")
                self.publish_error(task_id, e)
                break

        # 清理队列
        self._cleanup_queue(task_id)
        elapsed = time.time() - start_time
        logger.info(f"✅ Stopped listening for task {str(task_id)[:8]}... (elapsed: {elapsed:.2f}s)")

    def stop_listen(self, task_id: UUID) -> None:
        """停止监听队列"""
        # 发送停止信号（None）
        self.queue(task_id).put(None)

    def _cleanup_queue(self, task_id: UUID) -> None:
        """清理队列资源"""
        task_id_str = str(task_id)
        if task_id_str in self._queues:
            # 清空队列中的剩余项
            queue = self._queues[task_id_str]
            while not queue.empty():
                try:
                    queue.get_nowait()
                except Empty:
                    break

            # 删除队列
            del self._queues[task_id_str]
            logger.debug(f"🧹 Cleaned up queue for task {task_id_str[:8]}...")

    def get_active_tasks(self) -> list:
        """获取当前活跃的任务列表"""
        return list(self._queues.keys())

    def clear_all(self) -> None:
        """清理所有队列（用于测试或重置）"""
        for task_id_str in list(self._queues.keys()):
            self._cleanup_queue(UUID(task_id_str))
        logger.info("🧹 Cleared all queues")
