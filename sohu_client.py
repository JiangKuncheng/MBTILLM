# -*- coding: utf-8 -*-
"""
SohuGlobal API客户端 - 完整版本
支持加密认证和所有接口
"""

import logging
import asyncio
import aiohttp
import json
import hashlib
import hmac
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

logger = logging.getLogger(__name__)

class SohuAPIClient:
    """SohuGlobal API客户端 - 完整版本"""
    
    def __init__(self):
        # 新的接口地址
        self.base_url = "http://192.168.150.252:888"
        self.timeout = 15
        self.max_retries = 3
        self.session = None
        
        # 加密参数
        self.hmac_key = None
        self.aes_key = None
        self.iv = None
        
        logger.info("完整版SohuGlobal API客户端初始化完成")
    
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
    
    async def _get_encryption_keys(self) -> bool:
        """获取加密密钥"""
        try:
            url = f"{self.base_url}/app/v1/query/aesKey"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        data = result.get("data", {})
                        self.hmac_key = data.get("hmacKey")
                        self.aes_key = data.get("aesKey")
                        self.iv = data.get("iv")
                        
                        if self.hmac_key and self.aes_key and self.iv:
                            logger.info("成功获取加密密钥")
                            return True
                
                logger.error(f"获取加密密钥失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"获取加密密钥异常: {e}")
            return False
    
    def _generate_nonce(self) -> str:
        """生成随机字符串，不低于18位"""
        return str(uuid.uuid4()).replace('-', '') + str(int(time.time() * 1000))[-6:]
    
    def _get_encrypt_data(self, url: str) -> Dict[str, Any]:
        """获取加密数据 - 完全对应前端的getEncryptData函数"""
        # 构建参数（与前端完全一致）
        obj = {
            "token": "",  # 非登录接口可为空字符串
            "userId": 0,    # 非登录接口可为0
            "timestamp": int(time.time() * 1000),
            "url": url,
            "platform": "web",
            "nonce": self._generate_nonce(),
        }
        
        # 过滤并排序参数（排除sign字段）
        filtered_params = {}
        for key in sorted(obj.keys()):
            if key != "sign" and obj[key] is not None:
                filtered_params[key] = obj[key]
        
        # 拼接键值对，最后加上key=hmacKey
        query_string = ""
        for key, value in filtered_params.items():
            query_string += f"{key}={value}&"
        query_string += f"key={self.hmac_key}"
        
        # 计算HMAC-SHA256签名
        hmac_obj = hmac.new(
            self.hmac_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        )
        signature = hmac_obj.hexdigest()
        
        obj["sign"] = signature
        return obj
    
    def _get_encrypt(self, data: str) -> str:
        """获取加密字符串 - 对应前端的getEncrypt函数"""
        if not self.aes_key or not self.iv:
            raise ValueError("AES密钥或IV未设置")
        
        # AES加密
        cipher = AES.new(
            self.aes_key.encode('utf-8'),
            AES.MODE_CBC,
            self.iv.encode('utf-8')
        )
        
        # 填充数据
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _get_decrypt(self, encrypted_data: str) -> str:
        """解密字符串"""
        if not self.aes_key or not self.iv:
            raise ValueError("AES密钥或IV未设置")
        
        # AES解密
        cipher = AES.new(
            self.aes_key.encode('utf-8'),
            AES.MODE_CBC,
            self.iv.encode('utf-8')
        )
        
        # 解密
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = cipher.decrypt(encrypted_bytes)
        
        # 去除填充
        return unpad(decrypted, AES.block_size).decode('utf-8')
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Dict = None, params: Dict = None,
                          headers: Dict = None, use_encryption: bool = True) -> Dict[str, Any]:
        """发起HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 准备请求头
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        
        # 如果需要加密认证
        if use_encryption and self.hmac_key:
            encrypt_data = self._get_encrypt_data(endpoint)
            
            # 将加密数据JSON序列化后用AES加密，作为x-encrypt-key请求头发送
            json_data = json.dumps(encrypt_data, ensure_ascii=False)
            encrypted_key = self._get_encrypt(json_data)
            
            request_headers["x-encrypt-key"] = encrypted_key
            
            # 调试信息
            logger.debug(f"加密数据: {encrypt_data}")
            logger.debug(f"JSON数据: {json_data}")
            logger.debug(f"加密后的key: {encrypted_key}")
            logger.debug(f"加密请求头: {request_headers}")
        
        # 重试逻辑
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    async with self.session.get(url, params=params, headers=request_headers) as response:
                        if response.status == 200:
                            try:
                                result = await response.json()
                                return result
                            except:
                                text = await response.text()
                                return {"code": 200, "data": text, "msg": "返回文本内容"}
                        else:
                            text = await response.text()
                            logger.warning(f"API请求失败: HTTP {response.status}, {text}")
                            return {"code": response.status, "msg": text}
                
                elif method.upper() == "POST":
                    async with self.session.post(url, json=data, params=params, headers=request_headers) as response:
                        if response.status == 200:
                            try:
                                result = await response.json()
                                return result
                            except:
                                text = await response.text()
                                return {"code": 200, "data": text, "msg": "返回文本内容"}
                        else:
                            text = await response.text()
                            logger.warning(f"API请求失败: HTTP {response.status}, {text}")
                            return {"code": response.status, "msg": text}
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
            except asyncio.TimeoutError:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"请求异常 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(1)
    
    async def _ensure_encryption_ready(self) -> bool:
        """确保加密参数已准备"""
        if self.hmac_key and self.aes_key and self.iv:
            return True
        
        # 获取加密密钥
        return await self._get_encryption_keys()
    
    # =============================================================================
    # 内容获取接口
    # =============================================================================
    
    async def get_articles(self, page: int = 1, size: int = 10, 
                          keyword: str = None, category_id: int = None) -> Dict[str, Any]:
        """获取文章列表 - 新接口"""
        params = {"page": page, "size": size}
        if keyword:
            params["keyword"] = keyword
        if category_id:
            params["categoryId"] = category_id
        
        try:
            response = await self._make_request("GET", "/app/api/content/article/", params=params)
            logger.info(f"获取文章列表: 页码={page}, 数量={size}")
            return response
        except Exception as e:
            logger.error(f"获取文章列表失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_article_detail(self, article_id: int) -> Dict[str, Any]:
        """获取文章详情 - 新接口"""
        if not await self._ensure_encryption_ready():
            return {"code": 401, "msg": "加密参数获取失败"}
        
        try:
            response = await self._make_request("GET", f"/app/api/content/article/{article_id}")
            logger.info(f"获取文章详情: ID={article_id}")
            return response
        except Exception as e:
            logger.error(f"获取文章详情失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def search_articles(self, keyword: str, page: int = 1, size: int = 10) -> Dict[str, Any]:
        """搜索文章 - 新接口"""
        if not await self._ensure_encryption_ready():
            return {"code": 401, "msg": "加密参数获取失败"}
        
        params = {
            "keyword": keyword,
            "page": page,
            "size": size
        }
        
        try:
            response = await self._make_request("GET", "/app/api/content/article/search", params=params)
            logger.info(f"搜索文章: 关键词={keyword}, 页码={page}")
            return response
        except Exception as e:
            logger.error(f"搜索文章失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    async def get_categories(self) -> Dict[str, Any]:
        """获取文章分类 - 新接口"""
        if not await self._ensure_encryption_ready():
            return {"code": 401, "msg": "加密参数获取失败"}
        
        try:
            response = await self._make_request("GET", "/app/api/content/category/")
            logger.info("获取文章分类")
            return response
        except Exception as e:
            logger.error(f"获取文章分类失败: {e}")
            return {"code": 500, "msg": f"请求失败: {str(e)}"}
    
    # =============================================================================
    # 批量获取和分页获取
    # =============================================================================
    
    async def get_all_articles(self, max_pages: int = 10, page_size: int = 20) -> List[Dict[str, Any]]:
        """获取所有文章"""
        all_articles = []
        
        for page in range(1, max_pages + 1):
            try:
                response = await self.get_articles(page=page, size=page_size)
                
                if response.get("code") == 200:
                    data = response.get("data", [])
                    
                    if not data:
                        logger.info(f"第{page}页没有更多文章")
                        break
                    
                    all_articles.extend(data)
                    logger.info(f"获取文章第{page}页: {len(data)}条")
                    
                    # 如果返回的数据少于页面大小，说明是最后一页
                    if len(data) < page_size:
                        break
                        
                else:
                    logger.warning(f"获取文章第{page}页失败: {response}")
                    break
                    
            except Exception as e:
                logger.error(f"获取文章第{page}页异常: {e}")
                break
            
            # 避免请求过快
            await asyncio.sleep(0.1)
        
        logger.info(f"总共获取文章: {len(all_articles)}条")
        return all_articles
    
    async def get_articles_by_category(self, category_id: int, max_pages: int = 5, page_size: int = 20) -> List[Dict[str, Any]]:
        """根据分类获取文章"""
        all_articles = []
        
        for page in range(1, max_pages + 1):
            try:
                response = await self.get_articles(page=page, size=page_size, category_id=category_id)
                
                if response.get("code") == 200:
                    data = response.get("data", [])
                    
                    if not data:
                        logger.info(f"分类{category_id}第{page}页没有更多文章")
                        break
                    
                    all_articles.extend(data)
                    logger.info(f"获取分类{category_id}第{page}页: {len(data)}条")
                    
                    if len(data) < page_size:
                        break
                        
                else:
                    logger.warning(f"获取分类{category_id}第{page}页失败: {response}")
                    break
                    
            except Exception as e:
                logger.error(f"获取分类{category_id}第{page}页异常: {e}")
                break
            
            await asyncio.sleep(0.1)
        
        logger.info(f"分类{category_id}总共获取文章: {len(all_articles)}条")
        return all_articles
    
    # =============================================================================
    # 测试方法
    # =============================================================================
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            # 尝试获取文章列表
            articles = await self.get_articles(page=1, size=5)
            return {
                "success": True,
                "message": "连接成功",
                "test_result": articles
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}",
                "error": str(e)
            }
    
    async def test_encryption(self) -> Dict[str, Any]:
        """测试加密功能"""
        try:
            if await self._ensure_encryption_ready():
                # 测试加密
                test_string = "Hello, Sohu API!"
                encrypted = self._get_encrypt(test_string)
                decrypted = self._get_decrypt(encrypted)
                
                return {
                    "success": True,
                    "message": "加密功能正常",
                    "encryption_keys": {
                        "hmac_key": self.hmac_key[:20] + "..." if self.hmac_key else None,
                        "aes_key": self.aes_key,
                        "iv": self.iv
                    },
                    "test_result": {
                        "original": test_string,
                        "encrypted": encrypted,
                        "decrypted": decrypted,
                        "match": test_string == decrypted
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "加密参数获取失败"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"加密测试失败: {str(e)}",
                "error": str(e)
            }

# 创建全局客户端实例
sohu_client = SohuAPIClient()

# 测试函数
async def test_full_sohu_client():
    """测试完整版搜狐客户端"""
    async with sohu_client as client:
        try:
            # 测试连接
            result = await client.test_connection()
            print("连接测试结果:", json.dumps(result, indent=2, ensure_ascii=False))
            
            # 测试加密功能
            encrypt_result = await client.test_encryption()
            print("\n加密测试结果:", json.dumps(encrypt_result, indent=2, ensure_ascii=False))
            
            if result["success"] and encrypt_result["success"]:
                # 获取文章列表
                articles = await client.get_articles(page=1, size=10)
                print("\n文章列表:", json.dumps(articles, indent=2, ensure_ascii=False))
                
                # 测试加密接口
                print("\n测试加密接口...")
                
                # 获取分类
                categories = await client.get_categories()
                print("\n分类列表:", json.dumps(categories, indent=2, ensure_ascii=False))
                
                # 搜索文章
                search_result = await client.search_articles("测试", page=1, size=5)
                print("\n搜索结果:", json.dumps(search_result, indent=2, ensure_ascii=False))
                
                # 如果有文章，尝试获取详情
                if articles and "data" in articles and "list" in articles["data"]:
                    article_list = articles["data"]["list"]
                    if article_list:
                        first_article = article_list[0]
                        article_id = first_article.get("id")
                        if article_id:
                            print(f"\n获取文章详情 (ID: {article_id})...")
                            detail = await client.get_article_detail(article_id)
                            print(f"文章详情: {json.dumps(detail, indent=2, ensure_ascii=False)}")
                
        except Exception as e:
            print(f"测试失败: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_full_sohu_client())
