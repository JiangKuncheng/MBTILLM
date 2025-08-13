# -*- coding: utf-8 -*-
"""
SohuGlobal API客户端
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from new_config import CONFIG

logger = logging.getLogger(__name__)

class SohuAPIClient:
    """SohuGlobal API客户端"""
    
    def __init__(self):
        self.base_url = CONFIG["sohu_api"]["base_url"]
        self.phone = CONFIG["sohu_api"]["login_phone"]
        self.password = CONFIG["sohu_api"]["login_password"]
        self.timeout = CONFIG["sohu_api"]["timeout"]
        self.max_retries = CONFIG["sohu_api"]["max_retries"]
        
        self.token = None
        self.token_expires_at = None
        self.session = None
        
        logger.info("SohuGlobal API客户端初始化完成")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Dict = None, params: Dict = None,
                          headers: Dict = None) -> Dict[str, Any]:
        """发起HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 准备请求头
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        
        # 添加认证Token
        if self.token and endpoint != "/api/user/login":
            request_headers["Authorization"] = f"Bearer {self.token}"
        
        # 重试逻辑
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    async with self.session.get(url, params=params, headers=request_headers) as response:
                        result = await response.json()
                elif method.upper() == "POST":
                    async with self.session.post(url, json=data, params=params, headers=request_headers) as response:
                        result = await response.json()
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                # 检查响应状态
                if result.get("code") == 200:
                    return result
                elif result.get("code") == 401:
                    # Token过期，尝试重新登录
                    if await self._login():
                        continue  # 重试请求
                    else:
                        raise Exception("登录失败，无法获取有效Token")
                else:
                    logger.warning(f"API请求失败: {result}")
                    return result
                
            except asyncio.TimeoutError:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(1)  # 等待1秒后重试
            
            except Exception as e:
                logger.error(f"请求异常 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(1)
    
    async def _login(self) -> bool:
        """登录获取Token"""
        try:
            login_data = {
                "phone": self.phone,
                "password": self.password
            }
            
            response = await self._make_request("POST", "/api/user/login", data=login_data)
            
            if response.get("code") == 200:
                user_data = response.get("data", {})
                self.token = user_data.get("token")
                
                if self.token:
                    # 设置Token过期时间（假设24小时有效）
                    self.token_expires_at = time.time() + 24 * 3600
                    logger.info("SohuGlobal API登录成功")
                    return True
            
            logger.error(f"登录失败: {response}")
            return False
            
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False
    
    async def _ensure_authenticated(self) -> bool:
        """确保已认证"""
        # 检查Token是否存在且未过期
        if self.token and self.token_expires_at and time.time() < self.token_expires_at:
            return True
        
        # 尝试登录
        return await self._login()
    
    # =============================================================================
    # 内容获取接口
    # =============================================================================
    
    async def get_articles(self, page: int = 1, size: int = 10, 
                          keyword: str = None, category_id: int = None) -> Dict[str, Any]:
        """获取文章列表"""
        if not await self._ensure_authenticated():
            return {"code": 401, "msg": "认证失败"}
        
        params = {"page": page, "size": size}
        if keyword:
            params["keyword"] = keyword
        if category_id:
            params["categoryId"] = category_id
        
        try:
            response = await self._make_request("GET", "/api/article/list", params=params)
            logger.info(f"获取文章列表: 页码={page}, 数量={size}")
            return response
        except Exception as e:
            logger.error(f"获取文章列表失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_article_detail(self, article_id: int) -> Dict[str, Any]:
        """获取文章详情"""
        if not await self._ensure_authenticated():
            return {"code": 401, "msg": "认证失败"}
        
        try:
            response = await self._make_request("GET", f"/api/article/{article_id}")
            logger.info(f"获取文章详情: ID={article_id}")
            return response
        except Exception as e:
            logger.error(f"获取文章详情失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_videos(self, page: int = 1, size: int = 10,
                        keyword: str = None, category_id: int = None) -> Dict[str, Any]:
        """获取视频列表"""
        if not await self._ensure_authenticated():
            return {"code": 401, "msg": "认证失败"}
        
        params = {"page": page, "size": size}
        if keyword:
            params["keyword"] = keyword
        if category_id:
            params["categoryId"] = category_id
        
        try:
            response = await self._make_request("GET", "/api/video/list", params=params)
            logger.info(f"获取视频列表: 页码={page}, 数量={size}")
            return response
        except Exception as e:
            logger.error(f"获取视频列表失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_video_detail(self, video_id: int) -> Dict[str, Any]:
        """获取视频详情"""
        if not await self._ensure_authenticated():
            return {"code": 401, "msg": "认证失败"}
        
        try:
            response = await self._make_request("GET", f"/api/video/{video_id}")
            logger.info(f"获取视频详情: ID={video_id}")
            return response
        except Exception as e:
            logger.error(f"获取视频详情失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_products(self, page: int = 1, size: int = 10,
                          keyword: str = None, category_id: int = None) -> Dict[str, Any]:
        """获取商品列表"""
        if not await self._ensure_authenticated():
            return {"code": 401, "msg": "认证失败"}
        
        params = {"page": page, "size": size}
        if keyword:
            params["keyword"] = keyword
        if category_id:
            params["categoryId"] = category_id
        
        try:
            response = await self._make_request("GET", "/api/product/list", params=params)
            logger.info(f"获取商品列表: 页码={page}, 数量={size}")
            return response
        except Exception as e:
            logger.error(f"获取商品列表失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_product_detail(self, product_id: int) -> Dict[str, Any]:
        """获取商品详情"""
        if not await self._ensure_authenticated():
            return {"code": 401, "msg": "认证失败"}
        
        try:
            response = await self._make_request("GET", f"/api/product/{product_id}")
            logger.info(f"获取商品详情: ID={product_id}")
            return response
        except Exception as e:
            logger.error(f"获取商品详情失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    # =============================================================================
    # 内容获取批量接口
    # =============================================================================
    
    async def get_content_by_id(self, content_id: int, content_type: str = None) -> Dict[str, Any]:
        """根据ID获取内容详情（自动判断类型）"""
        # 如果指定了类型，直接调用对应接口
        if content_type == "article":
            return await self.get_article_detail(content_id)
        elif content_type == "video":
            return await self.get_video_detail(content_id)
        elif content_type == "product":
            return await self.get_product_detail(content_id)
        
        # 否则尝试各种类型
        for content_type, method in [
            ("article", self.get_article_detail),
            ("video", self.get_video_detail),
            ("product", self.get_product_detail)
        ]:
            try:
                result = await method(content_id)
                if result.get("code") == 200:
                    # 在返回数据中添加类型信息
                    if "data" in result and result["data"]:
                        result["data"]["content_type"] = content_type
                    return result
            except Exception as e:
                logger.debug(f"尝试获取{content_type} {content_id}失败: {e}")
                continue
        
        return {"code": 404, "msg": "内容不存在"}
    
    async def get_contents_batch(self, content_ids: List[int], 
                               content_type: str = None) -> Dict[str, Any]:
        """批量获取内容详情"""
        if not content_ids:
            return {"code": 400, "msg": "内容ID列表为空"}
        
        results = {"contents": [], "total_requested": len(content_ids), "missing_ids": []}
        
        # 并发获取内容
        tasks = []
        for content_id in content_ids:
            task = self.get_content_by_id(content_id, content_type)
            tasks.append((content_id, task))
        
        # 执行并发请求
        responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # 处理结果
        for (content_id, _), response in zip(tasks, responses):
            if isinstance(response, Exception):
                logger.error(f"获取内容 {content_id} 异常: {response}")
                results["missing_ids"].append(content_id)
            elif response.get("code") == 200 and response.get("data"):
                results["contents"].append(response["data"])
            else:
                logger.warning(f"内容 {content_id} 获取失败: {response}")
                results["missing_ids"].append(content_id)
        
        results["total_found"] = len(results["contents"])
        
        return {
            "code": 200,
            "msg": "批量获取完成",
            "data": results
        }
    
    # =============================================================================
    # 内容搜索和分页获取
    # =============================================================================
    
    async def fetch_all_content_by_type(self, content_type: str, 
                                       max_pages: int = 10, 
                                       page_size: int = 20) -> List[Dict[str, Any]]:
        """获取指定类型的所有内容"""
        all_contents = []
        
        # 选择对应的获取方法
        if content_type == "article":
            fetch_method = self.get_articles
        elif content_type == "video":
            fetch_method = self.get_videos
        elif content_type == "product":
            fetch_method = self.get_products
        else:
            logger.error(f"不支持的内容类型: {content_type}")
            return []
        
        # 分页获取
        for page in range(1, max_pages + 1):
            try:
                response = await fetch_method(page=page, size=page_size)
                
                if response.get("code") == 200:
                    data = response.get("data", {})
                    contents = data.get("list", [])
                    
                    if not contents:
                        logger.info(f"第{page}页没有更多{content_type}内容")
                        break
                    
                    # 添加内容类型标识
                    for content in contents:
                        content["content_type"] = content_type
                    
                    all_contents.extend(contents)
                    logger.info(f"获取{content_type}第{page}页: {len(contents)}条内容")
                    
                    # 检查是否还有更多页
                    total_pages = data.get("pages", 0)
                    if page >= total_pages:
                        logger.info(f"{content_type}内容获取完成，总页数: {total_pages}")
                        break
                        
                else:
                    logger.warning(f"获取{content_type}第{page}页失败: {response}")
                    break
                    
            except Exception as e:
                logger.error(f"获取{content_type}第{page}页异常: {e}")
                break
            
            # 避免请求过快
            await asyncio.sleep(0.1)
        
        logger.info(f"总共获取{content_type}内容: {len(all_contents)}条")
        return all_contents
    
    async def fetch_all_contents(self, max_pages_per_type: int = 5,
                               page_size: int = 20) -> List[Dict[str, Any]]:
        """获取所有类型的内容"""
        all_contents = []
        
        content_types = ["article", "video", "product"]
        
        # 并发获取各类型内容
        tasks = []
        for content_type in content_types:
            task = self.fetch_all_content_by_type(content_type, max_pages_per_type, page_size)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"获取{content_types[i]}内容异常: {result}")
            else:
                all_contents.extend(result)
        
        logger.info(f"总共获取内容: {len(all_contents)}条")
        return all_contents

# 创建全局客户端实例
sohu_client = SohuAPIClient()
