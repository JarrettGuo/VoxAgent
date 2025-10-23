#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : qiniu_client.py
"""

import json
from typing import Optional, Dict, Any

import requests

from src.utils.logger import logger


class QiniuClient:
    """
    七牛云 API 客户端基类
    统一管理 API Key 和请求
    """

    def __init__(self, api_key: str):
        """初始化七牛云客户端"""
        self.api_key = api_key
        self.base_url = "https://openai.qiniu.com/v1"

        if not api_key:
            raise ValueError("API Key 不能为空")

        logger.info("✅ Qiniu Client initialized successfully")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _make_request(
            self,
            method: str,
            endpoint: str,
            data: Optional[Dict[str, Any]] = None,
            timeout: int = 30
    ) -> Dict[str, Any]:
        """发送 HTTP 请求，并处理响应"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Don't support HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout occurred after {timeout} seconds")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP Request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"   Response: {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            raise
