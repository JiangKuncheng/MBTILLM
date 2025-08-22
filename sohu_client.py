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
import base64

logger = logging.getLogger(__name__)

class SohuAPIClient:
    """SohuGlobal API客户端 - 完整版本"""
    
    def __init__(self):
        # 从配置文件获取接口地址，如果没有则使用默认值
        try:
            from new_config import CONFIG
            self.base_url = CONFIG.get("sohu_api", {}).get("base_url", "http://192.168.150.252:8080")
        except ImportError:
            # 如果无法导入配置，使用默认地址
            self.base_url = "http://192.168.150.252:8080"
        
        self.timeout = 15
        self.max_retries = 3
        self.session = None
        
        # 用户认证信息（模拟前端store的数据）
        self.access_token = None
        self.user_id = 0
        self.hmac_key = None
        self.aes_key = None
        self.iv = None
        
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
        """获取加密密钥和用户认证信息"""
        try:
            url = f"{self.base_url}/app/v1/query/aesKey"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        data = result.get("data", {})
                        # 获取加密密钥
                        self.hmac_key = data.get("hmacKey")
                        self.aes_key = data.get("aesKey")
                        self.iv = data.get("iv")
                        
                        # 获取用户认证信息（这里需要根据实际情况调整）
                        # 通常这些信息应该从登录接口获取
                        self.access_token = data.get("accessToken")  # 可能为空
                        self.user_id = data.get("userId", 0)  # 可能为0
                        
                        if self.hmac_key and self.aes_key and self.iv:
                            logger.info("成功获取加密密钥和认证信息")
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
            "token": self.access_token or "",  # 使用实际的accessToken
            "userId": self.user_id or 0,    # 使用实际的userId
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
        
        # 计算HMAC-SHA256签名 - 使用与前端完全一致的方式
        # 注意：这里需要确保编码方式一致
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
        
        # 完全按照前端逻辑实现
        # 前端使用 CryptoJS.enc.Latin1.parse(aesKey) 和 CryptoJS.enc.Utf8.parse(iv)
        
        # 1. 将数据转换为UTF-8字节
        data_bytes = data.encode('utf-8')
        
        # 2. 将AES密钥转换为Latin1编码（对应前端的CryptoJS.enc.Latin1.parse）
        aes_key_bytes = self.aes_key.encode('latin1')
        
        # 3. 将IV转换为UTF-8编码（对应前端的CryptoJS.enc.Utf8.parse）
        iv_bytes = self.iv.encode('utf-8')
        
        # 4. 创建AES加密器
        cipher = AES.new(
            aes_key_bytes,
            AES.MODE_CBC,
            iv_bytes
        )
        
        # 5. 使用ZeroPadding（对应前端的CryptoJS.pad.ZeroPadding）
        block_size = AES.block_size
        padding_length = block_size - (len(data_bytes) % block_size)
        
        if padding_length == block_size:
            padding_length = 0
            
        # 添加零填充
        padded_data = data_bytes + b'\x00' * padding_length
        encrypted = cipher.encrypt(padded_data)
        
        # 6. Base64编码（对应前端的encrypted.toString()）
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
        
        # 去除零填充
        # 找到最后一个非零字节
        while decrypted and decrypted[-1] == 0:
            decrypted = decrypted[:-1]
            
        return decrypted.decode('utf-8')
    
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
        # 每次都重新获取加密密钥，不使用缓存
        # 这样可以确保每次请求都使用最新的密钥
        return await self._get_encryption_keys()
    
    async def _ensure_auth_ready(self) -> bool:
        """确保认证已准备"""
        # 检查是否有必要的认证信息
        if not (self.hmac_key and self.aes_key and self.iv):
            return False
        
        # 如果没有token和userId，尝试登录
        if not self.access_token or not self.user_id:
            logger.info("缺少认证信息，尝试登录...")
            if await self.login():
                return True
            else:
                logger.error("登录失败")
                return False
        
        return True
    
    async def login(self, username: str = "admin", password: str = "123456") -> bool:
        """登录获取token和userId - 注意：登录接口不需要加密认证"""
        try:
            url = f"{self.base_url}/auth/v2/login"
            
            # 登录请求数据 - 完全按照你同事的格式
            login_data = {
                "userName": username,  # 使用userName
                "password": password,  # 暂时使用明文，后续可能需要加密
                "loginType": "PASSWORD",
                "deviceType": "PC"  # 添加deviceType
            }
            
            headers = {
                "Content-Type": "application/json",
                "syssource": "sohuglobal",  # 添加重要的syssource头
                "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
                "Accept": "*/*",
                "Host": "192.168.150.252:8080",
                "Connection": "keep-alive"
            }
            
            # 调试：打印登录请求
            logger.info(f"self.base_url: {self.base_url}")
            logger.info(f"登录请求URL: {url}")
            logger.info(f"登录请求数据: {json.dumps(login_data, indent=2, ensure_ascii=False)}")
            logger.info(f"登录请求头: {headers}")
            
            async with self.session.post(url, json=login_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        data = result.get("data", {})
                        self.access_token = data.get("accessToken")
                        self.user_id = data.get("userId")
                        logger.info(f"登录成功: accessToken={self.access_token}, userId={self.user_id}")
                        return True
                    else:
                        logger.error(f"登录失败: {result.get('msg')}")
                        return False
                else:
                    logger.error(f"登录请求失败: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False
    
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
    
    async def get_content_by_id(self, content_id: int, content_type: str = "article") -> Dict[str, Any]:
        """根据ID获取内容详情"""
        # 确保加密参数已准备
        if not await self._ensure_encryption_ready():
            return {"code": 401, "msg": "加密参数获取失败"}
        
        try:
            # 构建请求URL - 根据你提供的接口地址
            url = f"{self.base_url}/app/api/content/article/{content_id}"
            
            # 获取加密数据
            # 只使用相对路径，不包含base_url
            relative_path = f"/app/api/content/article/{content_id}"
            encrypt_data = self._get_encrypt_data(relative_path)
            
            # 发送请求
            # 先将字典转换为JSON字符串，然后加密
            json_data = json.dumps(encrypt_data, ensure_ascii=False)
            encrypted_data = self._get_encrypt(json_data)
            
            # 使用登录后获取的真实token
            auth_token = f"Bearer {self.access_token}" if self.access_token else ""
            logger.info(f"使用认证token: {auth_token}")
            
            headers = {
                "Content-Type": "application/json",
                "x-encrypt-key": encrypted_data,
                "Version": "1.5.0",
                "Authorization": auth_token
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    # 检查响应类型
                    content_type = response.headers.get('content-type', '')
                    logger.info(f"响应类型: {content_type}")
                    
                    try:
                        if 'text/plain' in content_type:
                            # 如果是text/plain，先获取文本内容
                            text_content = await response.text()
                            logger.info(f"收到text/plain响应: {text_content}")
                            
                            # 尝试解析JSON
                            try:
                                result = json.loads(text_content)
                                logger.info(f"成功解析JSON: {result}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON解析失败: {e}")
                                return {"code": 200, "msg": "响应解析成功", "data": text_content, "raw_content": text_content}
                        else:
                            # 正常JSON响应
                            result = await response.json()
                            logger.info(f"获取内容 {content_id} 成功")
                            return result
                    except Exception as e:
                        logger.error(f"响应处理异常: {e}")
                        return {"code": 500, "msg": f"响应处理异常: {str(e)}"}
                else:
                    logger.error(f"获取内容 {content_id} 失败: HTTP {response.status}")
                    return {"code": response.status, "msg": "HTTP请求失败"}
                    
        except Exception as e:
            logger.error(f"获取内容 {content_id} 异常: {e}")
            return {"code": 500, "msg": f"请求异常: {str(e)}"}
    
    async def get_article_list(self, page_num: int = 1, page_size: int = 20, 
                              site_id: Optional[int] = None, state: Optional[str] = None,
                              category_id: Optional[int] = None) -> Dict[str, Any]:
        """获取图文列表 - 搜狐接口"""
        # 确保加密参数已准备
        if not await self._ensure_encryption_ready():
            return {"code": 401, "msg": "加密参数获取失败"}
        
        # 确保认证已准备
        if not await self._ensure_auth_ready():
            return {"code": 401, "msg": "需要认证才能访问接口"}
        
        try:
            # 构建请求URL - 添加/app前缀
            url = f"{self.base_url}/app/api/content/article/list"
            
            # 构建查询参数
            params = {
                "pageNum": page_num,
                "pageSize": page_size,
                "aiRec": "false",  # 固定传"false"字符串，否则每次推荐结果一样
            }
            
            # 添加可选参数
            if site_id is not None:
                params["siteId"] = site_id
            if state is not None:
                params["state"] = state
            if category_id is not None:
                params["categoryId"] = category_id
            
            # 获取加密数据
            # 只使用相对路径，不包含base_url
            relative_path = f"/api/content/article/list?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            encrypt_data = self._get_encrypt_data(relative_path)
            
            # 调试：打印加密数据
            logger.info(f"加密数据: {json.dumps(encrypt_data, indent=2, ensure_ascii=False)}")
            
            # 发送请求
            # 使用登录后的真实token和加密数据
            # 先将字典转换为JSON字符串，然后加密
            json_data = json.dumps(encrypt_data, ensure_ascii=False)
            encrypted_data = self._get_encrypt(json_data)
            
            # 使用登录后获取的真实token
            auth_token = f"Bearer {self.access_token}" if self.access_token else ""
            logger.info(f"使用认证token: {auth_token}")
            
            headers = {
                "Content-Type": "application/json",
                "x-encrypt-key": encrypted_data,
                "Version": "1.5.0",
                "Authorization": auth_token
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    # 检查响应类型
                    content_type = response.headers.get('content-type', '')
                    logger.info(f"响应类型: {content_type}")
                    
                    try:
                        if 'text/html' in content_type:
                            # 如果是text/html，先获取文本内容
                            text_content = await response.text()
                            logger.info(f"收到text/html响应: {text_content[:200]}...")  # 只显示前200个字符
                            
                            # 尝试解析JSON（可能HTML中包含JSON）
                            try:
                                result = json.loads(text_content)
                                logger.info(f"成功解析JSON: {result}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON解析失败: {e}")
                                return {"code": 200, "msg": "响应解析成功", "data": text_content, "raw_content": text_content}
                        elif 'text/plain' in content_type:
                            # 如果是text/plain，先获取文本内容
                            text_content = await response.text()
                            logger.info(f"收到text/plain响应: {text_content}")
                            
                            # 尝试解析JSON
                            try:
                                result = json.loads(text_content)
                                logger.info(f"成功解析JSON: {result}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON解析失败: {e}")
                                return {"code": 200, "msg": "响应解析成功", "data": text_content, "raw_content": text_content}
                        else:
                            # 正常JSON响应
                            result = await response.json()
                            logger.info(f"获取图文列表成功: 第{page_num}页，共{page_size}条")
                            return result
                    except Exception as e:
                        logger.error(f"响应处理异常: {e}")
                        return {"code": 500, "msg": f"响应处理异常: {str(e)}"}
                else:
                    logger.error(f"获取图文列表失败: HTTP {response.status}")
                    return {"code": response.status, "msg": "HTTP请求失败"}
                    
        except Exception as e:
            logger.error(f"获取图文列表异常: {e}")
            return {"code": 500, "msg": f"请求异常: {str(e)}"}
    
    async def get_contents_batch(self, content_ids: List[int]) -> Dict[str, Any]:
        """批量获取内容详情"""
        # 确保加密参数已准备
        if not await self._ensure_encryption_ready():
            return {"code": 401, "msg": "加密参数获取失败"}
        
        try:
            # 构建请求URL
            url = f"{self.base_url}/app/api/content/batch"
            
            # 获取加密数据
            encrypt_data = self._get_encrypt_data(url)
            
            # 构建请求体
            request_data = {
                "content_ids": content_ids
            }
            
            # 发送请求
            # 使用登录后的真实token和加密数据
            # 先将字典转换为JSON字符串，然后加密
            json_data = json.dumps(encrypt_data, ensure_ascii=False)
            encrypted_data = self._get_encrypt(json_data)
            
            # 使用登录后获取的真实token
            auth_token = f"Bearer {self.access_token}" if self.access_token else ""
            logger.info(f"使用认证token: {auth_token}")
            
            headers = {
                "Content-Type": "application/json",
                "x-encrypt-key": encrypted_data,
                "Version": "1.5.0",
                "Authorization": auth_token
            }
            
            async with self.session.post(url, json=request_data, headers=headers) as response:
                if response.status == 200:
                    # 检查响应类型
                    content_type = response.headers.get('content-type', '')
                    logger.info(f"响应类型: {content_type}")
                    
                    try:
                        if 'text/plain' in content_type:
                            # 如果是text/plain，先获取文本内容
                            text_content = await response.text()
                            logger.info(f"收到text/plain响应: {text_content}")
                            
                            # 尝试解析JSON
                            try:
                                result = json.loads(text_content)
                                logger.info(f"成功解析JSON: {result}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON解析失败: {e}")
                                return {"code": 200, "msg": "响应解析成功", "data": text_content, "raw_content": text_content}
                        else:
                            # 正常JSON响应
                            result = await response.json()
                            logger.info(f"批量获取 {len(content_ids)} 个内容成功")
                            return result
                    except Exception as e:
                        logger.error(f"响应处理异常: {e}")
                        return {"code": 500, "msg": f"响应处理异常: {str(e)}"}
                else:
                    logger.error(f"批量获取内容失败: HTTP {response.status}")
                    return {"code": response.status, "msg": "HTTP请求失败"}
                    
        except Exception as e:
            logger.error(f"批量获取内容异常: {e}")
            return {"code": 500, "msg": f"请求异常: {str(e)}"}

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
