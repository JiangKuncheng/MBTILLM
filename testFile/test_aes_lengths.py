#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同AES密钥长度的效果
"""

import asyncio
import json
import base64
from Crypto.Cipher import AES

def test_aes_encryption():
    """测试不同AES密钥长度"""
    print("🔐 测试不同AES密钥长度")
    print("=" * 50)
    
    # 测试数据
    test_data = '{"token": "", "userId": 0, "timestamp": 1234567890, "url": "/test", "platform": "web", "nonce": "test123", "sign": "test456"}'
    
    # 不同的密钥长度
    test_cases = [
        {
            "name": "16字节密钥 (AES-128)",
            "key": "0123456789abcdef",
            "iv": "56781234efghabcd"
        },
        {
            "name": "24字节密钥 (AES-192)",
            "key": "0123456789abcdef0123456789abcdef012345",
            "iv": "56781234efghabcd56781234efghabcd"
        },
        {
            "name": "32字节密钥 (AES-256)",
            "key": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "iv": "56781234efghabcd56781234efghabcd56781234efghabcd56781234efghabcd"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔗 测试: {test_case['name']}")
        print(f"   密钥长度: {len(test_case['key'])} 字节")
        print(f"   IV长度: {len(test_case['iv'])} 字节")
        
        try:
            # 将数据转换为UTF-8字节
            data_bytes = test_data.encode('utf-8')
            
            # 将AES密钥转换为Latin1编码
            aes_key_bytes = test_case['key'].encode('latin1')
            
            # 将IV转换为UTF-8编码
            iv_bytes = test_case['iv'].encode('utf-8')
            
            # 创建AES加密器
            cipher = AES.new(
                aes_key_bytes,
                AES.MODE_CBC,
                iv_bytes
            )
            
            # 使用ZeroPadding
            block_size = AES.block_size
            padding_length = block_size - (len(data_bytes) % block_size)
            
            if padding_length == block_size:
                padding_length = 0
                
            # 添加零填充
            padded_data = data_bytes + b'\x00' * padding_length
            encrypted = cipher.encrypt(padded_data)
            
            # Base64编码
            result = base64.b64encode(encrypted).decode('utf-8')
            
            print(f"   加密结果长度: {len(result)} 字符")
            print(f"   加密结果: {result[:50]}...")
            
        except Exception as e:
            print(f"   ❌ 加密失败: {e}")
    
    print("\n✅ AES密钥长度测试完成")

if __name__ == "__main__":
    test_aes_encryption() 