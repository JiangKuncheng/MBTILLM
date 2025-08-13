# -*- coding: utf-8 -*-
"""
大模型API调用封装
"""

import httpx
import json
import asyncio
from typing import Optional, Dict, Any
from config import API_CONFIG

class LLMClient:
    def __init__(self):
        self.api_url = API_CONFIG["base_url"]
        self.api_key = API_CONFIG["api_key"]
        self.model = API_CONFIG["model"]
        self.temperature = API_CONFIG["temperature"]
        self.max_tokens = API_CONFIG["max_tokens"]
        self.timeout = API_CONFIG["timeout"]
    
    async def call_llm_async(self, prompt: str, max_retries: int = 3) -> str:
        """
        异步调用大模型API
        
        Args:
            prompt: 输入提示词
            max_retries: 最大重试次数
            
        Returns:
            模型返回的文本内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.api_url, 
                        headers=headers, 
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                    
            except httpx.TimeoutException:
                print(f"请求超时，重试 {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise Exception("API请求超时")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                
            except httpx.HTTPStatusError as e:
                print(f"HTTP错误: {e.response.status_code}")
                if e.response.status_code == 429:  # 速率限制
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
                    
            except json.JSONDecodeError:
                print("响应JSON解析失败")
                raise Exception("API响应格式错误")
                
            except Exception as e:
                print(f"未知错误: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
    
    def call_llm_sync(self, prompt: str, max_retries: int = 3) -> str:
        """
        同步调用大模型API（基于异步实现）
        
        Args:
            prompt: 输入提示词
            max_retries: 最大重试次数
            
        Returns:
            模型返回的文本内容
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.call_llm_async(prompt, max_retries))
    
    async def batch_call_llm(self, prompts: list[str], max_concurrent: int = 5) -> list[str]:
        """
        批量异步调用大模型API
        
        Args:
            prompts: 提示词列表
            max_concurrent: 最大并发数
            
        Returns:
            模型返回结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_call(prompt):
            async with semaphore:
                return await self.call_llm_async(prompt)
        
        tasks = [limited_call(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

# 全局客户端实例
llm_client = LLMClient()