# -*- coding: utf-8 -*-
"""
MBTI评价服务
"""

import logging
import asyncio
import aiohttp
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

from new_config import CONFIG
from database_service import db_service
from sohu_client import sohu_client

logger = logging.getLogger(__name__)

class MBTIEvaluationService:
    """MBTI评价服务"""
    
    def __init__(self):
        self.api_key = CONFIG["siliconflow"]["api_key"]
        self.base_url = CONFIG["siliconflow"]["base_url"]
        self.model = CONFIG["siliconflow"]["model"]
        self.timeout = CONFIG["siliconflow"]["timeout"]
        self.max_retries = CONFIG["siliconflow"]["max_retries"]
        self.evaluation_prompt = CONFIG["mbti"]["evaluation_prompt"]
        
        logger.info("MBTI评价服务初始化完成")
    
    async def _call_llm_api(self, content: str) -> Dict[str, Any]:
        """调用真实的SiliconFlow LLM API进行MBTI评价"""
        import httpx
        import json
        from new_config import SILICONFLOW_CONFIG
        
        try:
            logger.info("调用真实的SiliconFlow LLM API")
            
            headers = {
                "Authorization": f"Bearer {SILICONFLOW_CONFIG['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": SILICONFLOW_CONFIG["model"],
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "temperature": 0.3,  # 降低随机性，提高一致性
                "max_tokens": 4000,  # 增加token数量，确保批量评分响应完整
                "timeout": SILICONFLOW_CONFIG["timeout"]
            }
            
            async with httpx.AsyncClient(timeout=SILICONFLOW_CONFIG["timeout"]) as client:
                response = await client.post(
                    f"{SILICONFLOW_CONFIG['base_url']}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("LLM API调用成功")
                    return result
                else:
                    logger.error(f"LLM API调用失败: {response.status_code} - {response.text}")
                    # 如果API调用失败，返回None让上层处理
                    return None
                    
        except httpx.TimeoutException:
            logger.error("LLM API请求超时")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP错误: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"LLM API调用异常: {e}")
            return None
    
    def _parse_mbti_response(self, llm_response: Dict[str, Any]) -> Dict[str, float]:
        """解析LLM响应中的MBTI概率"""
        try:
            # 提取消息内容
            choices = llm_response.get("choices", [])
            if not choices:
                raise ValueError("LLM响应中没有choices")
            
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("LLM响应内容为空")
            
            # 查找JSON格式的概率数据
            json_pattern = r'\{[^}]*"[EISNTFJP]"\s*:\s*[0-9.]+[^}]*\}'
            json_matches = re.findall(json_pattern, content)
            
            if json_matches:
                # 尝试解析第一个匹配的JSON
                json_str = json_matches[0]
                try:
                    probabilities = json.loads(json_str)
                    
                    # 验证是否包含所有8个维度
                    required_traits = ["E", "I", "S", "N", "T", "F", "J", "P"]
                    if all(trait in probabilities for trait in required_traits):
                        # 验证概率值是否合理
                        for trait in required_traits:
                            prob = probabilities[trait]
                            if not isinstance(prob, (int, float)) or prob < 0 or prob > 1:
                                raise ValueError(f"无效的概率值: {trait}={prob}")
                        
                        # 归一化概率对
                        normalized = self._normalize_probabilities(probabilities)
                        logger.info("成功解析MBTI概率分布")
                        return normalized
                        
                except json.JSONDecodeError:
                    pass
            
            # 尝试其他解析方法 - 支持带引号和不带引号的格式
            prob_pattern = r'([EISNTFJP])\s*:\s*([0-9]*\.?[0-9]+)'
            matches = re.findall(prob_pattern, content)
            
            if len(matches) >= 8:
                probabilities = {}
                for trait, prob_str in matches:
                    try:
                        prob = float(prob_str)
                        if 0 <= prob <= 1:
                            probabilities[trait] = prob
                    except ValueError:
                        continue
                
                # 检查是否有完整的8个维度
                required_traits = ["E", "I", "S", "N", "T", "F", "J", "P"]
                if all(trait in probabilities for trait in required_traits):
                    normalized = self._normalize_probabilities(probabilities)
                    logger.info("通过正则表达式解析MBTI概率分布")
                    return normalized
            
            # 如果都无法解析，返回默认值
            logger.warning(f"无法解析MBTI概率，使用默认值。原始响应: {content[:200]}...")
            
        except Exception as e:
            logger.error(f"解析MBTI响应异常: {e}")
        
        # 返回默认中性概率
        return {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
    
    def _normalize_probabilities(self, probabilities: Dict[str, float]) -> Dict[str, float]:
        """归一化MBTI概率，确保每对和为1.0"""
        normalized = probabilities.copy()
        
        pairs = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
        for pair in pairs:
            trait1, trait2 = pair
            total = normalized.get(trait1, 0.5) + normalized.get(trait2, 0.5)
            
            if total > 0:
                normalized[trait1] = normalized.get(trait1, 0.5) / total
                normalized[trait2] = normalized.get(trait2, 0.5) / total
            else:
                normalized[trait1] = 0.5
                normalized[trait2] = 0.5
        
        return normalized
    
    def _clean_content(self, content: str) -> str:
        """清理内容文本"""
        if not content:
            return ""
        
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 移除URL链接
        content = re.sub(r'https?://\S+', '', content)
        
        # 移除多余的空白字符
        content = re.sub(r'\s+', ' ', content)
        
        # 限制长度
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        return content.strip()
    
    async def evaluate_content_mbti(self, content: str, content_id: int = None,
                                  content_title: str = None, content_type: str = None) -> Dict[str, float]:
        """评价内容的MBTI特征"""
        # 清理内容
        cleaned_content = self._clean_content(content)
        
        if len(cleaned_content) < 10:
            logger.warning("内容太短，使用默认MBTI概率")
            return {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
        
        try:
            # 调用LLM API
            logger.info(f"开始评价内容MBTI特征，内容长度: {len(cleaned_content)}")
            llm_response = await self._call_llm_api(cleaned_content)
            
            # 解析MBTI概率
            probabilities = self._parse_mbti_response(llm_response)
            
            # 保存到数据库（如果提供了content_id）
            if content_id:
                db_service.save_content_mbti(
                    content_id=content_id,
                    probabilities=probabilities,
                    content_title=content_title,
                    content_type=content_type
                )
                logger.info(f"保存内容 {content_id} 的MBTI评价")
            
            return probabilities
            
        except Exception as e:
            logger.error(f"评价内容MBTI特征失败: {e}")
            # 返回默认值
            return {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
    
    async def evaluate_content_by_id(self, content_id: int, content_type: str = None) -> Dict[str, float]:
        """根据内容ID评价MBTI特征"""
        # 先检查数据库中是否已有评价
        existing_mbti = db_service.get_content_mbti(content_id)
        if existing_mbti:
            logger.info(f"内容 {content_id} 的MBTI评价已存在，直接返回")
            return existing_mbti.to_dict()["probabilities"]
        
        # 演示内容数据（用于搜狐API不可用时）
        demo_contents = {
            1001: {
                "title": "团队协作的力量",
                "content": "我真心喜欢和团队一起工作！今天我们小组讨论了新项目，每个人都积极发言，分享自己的想法。通过大家的集思广益，我们很快就找到了创新的解决方案。团队合作让我感到充满活力，看到每个人的贡献汇聚成最终成果真的很有成就感！",
                "type": "article"
            },
            1002: {
                "title": "独处思考的价值",
                "content": "我发现最好的想法往往在独处时产生。今天下午一个人在咖啡厅里静静思考，突然对复杂的技术问题有了新的理解。我喜欢这种深度思考的过程，能够完全沉浸在问题的本质中，不被外界干扰。独立分析让我能够看到别人忽略的细节。",
                "type": "article"
            },
            1003: {
                "title": "数据驱动的决策",
                "content": "在做重要决策时，我坚持用数据说话。通过收集相关指标、分析历史趋势、建立预测模型，我们能够做出更加理性和准确的判断。感性的直觉有时会误导我们，只有客观的逻辑分析才能确保决策的科学性和有效性。",
                "type": "article"
            },
            1004: {
                "title": "关怀他人的重要性",
                "content": "我始终相信，关心他人的感受比追求完美的逻辑更重要。在团队中，我经常会询问同事的想法，确保每个人都感到被尊重和理解。当有人遇到困难时，我会主动提供帮助和情感支持。人与人之间的温暖连接是工作和生活中最珍贵的财富。",
                "type": "article"
            },
            1005: {
                "title": "计划的重要性",
                "content": "我是一个非常有计划性的人，喜欢把所有事情都安排得井井有条。每天早上我都会制定详细的待办清单，按优先级排序任务。这样的安排让我能够高效地完成工作，避免遗漏重要事项。我认为良好的计划是成功的基础。",
                "type": "article"
            },
            1006: {
                "title": "拥抱变化与灵活性",
                "content": "我喜欢保持开放的心态，随时准备应对新的挑战和机会。当计划发生变化时，我会积极调整策略，寻找新的可能性。这种灵活性让我能够在不确定的环境中茁壮成长，把每一次变化都看作是学习和成长的机会。",
                "type": "article"
            }
        }
        
        # 检查是否是演示内容
        if content_id in demo_contents:
            demo_data = demo_contents[content_id]
            logger.info(f"使用演示内容 {content_id}: {demo_data['title']}")
            
            # 评价MBTI特征
            return await self.evaluate_content_mbti(
                content=demo_data["content"],
                content_id=content_id,
                content_title=demo_data["title"],
                content_type=demo_data["type"]
            )
        
        # 尝试从SohuGlobal API获取内容
        try:
            async with sohu_client as client:
                content_data = await client.get_content_by_id(content_id, content_type)
            
            if content_data.get("code") != 200:
                raise Exception(f"搜狐API返回错误: {content_data}")
            
            # 提取内容信息
            data = content_data["data"]
            content = data.get("content", "") or data.get("description", "")
            title = data.get("title", "")
            detected_type = data.get("content_type", content_type)
            
            if not content:
                raise Exception("内容为空")
            
            # 评价MBTI特征
            return await self.evaluate_content_mbti(
                content=content,
                content_id=content_id,
                content_title=title,
                content_type=detected_type
            )
            
        except Exception as e:
            logger.error(f"获取内容 {content_id} 失败: {e}")
            # 返回默认值
            return {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
    
    async def batch_evaluate_contents(self, contents: List[Dict], 
                                    max_concurrent: int = 3) -> Dict[str, Any]:
        """批量评价内容MBTI特征 - 一次最多同时调用三次大模型，循环完成
        
        Args:
            contents: 内容列表，每个内容包含 id, title, content 等字段
            max_concurrent: 最大并发数（最多3个）
            
        Returns:
            包含 results 数组的字典
        """
        logger.info(f"开始批量评价 {len(contents)} 个内容的MBTI特征")
        
        # 限制最大并发数为3
        max_concurrent = min(max_concurrent, 3)
        
        # 检查是否已有MBTI评分
        contents_to_evaluate = []
        cached_results = []
        
        for content in contents:
            content_id = content.get('id')
            existing_mbti = db_service.get_content_mbti(content_id)
            if existing_mbti:
                cached_results.append({
                    'id': content_id,
                    'title': content.get('title', ''),
                    'E_I': existing_mbti.E,
                    'S_N': existing_mbti.S,
                    'T_F': existing_mbti.T,
                    'J_P': existing_mbti.P,
                    'from_cache': True
                })
            else:
                contents_to_evaluate.append(content)
        
        logger.info(f"缓存内容: {len(cached_results)}, 需要评价: {len(contents_to_evaluate)}")
        
        if not contents_to_evaluate:
            logger.info("所有内容都已有MBTI评分，无需调用大模型")
            return {
                'results': cached_results,
                'total': len(contents),
                'successful': len(contents),
                'cached': len(cached_results),
                'new_evaluated': 0
            }
        
        # 分批处理，每批最多max_concurrent个内容
        batch_size = max_concurrent
        all_results = cached_results.copy()
        
        for i in range(0, len(contents_to_evaluate), batch_size):
            batch = contents_to_evaluate[i:i + batch_size]
            logger.info(f"处理第 {i//batch_size + 1} 批，包含 {len(batch)} 个内容")
            
            try:
                # 调用大模型进行批量评分
                batch_results = await self._batch_evaluate_with_llm(batch)
                
                if batch_results:
                    # 保存到数据库
                    for result in batch_results:
                        if result.get('success') and not result.get('from_cache'):
                            content_id = result.get('id')
                            probabilities = {
                                'E': result.get('E_I', 0.5),
                                'I': 1.0 - result.get('E_I', 0.5),
                                'S': result.get('S_N', 0.5),
                                'N': 1.0 - result.get('S_N', 0.5),
                                'T': result.get('T_F', 0.5),
                                'F': 1.0 - result.get('T_F', 0.5),
                                'J': result.get('J_P', 0.5),
                                'P': 1.0 - result.get('J_P', 0.5)
                            }
                            db_service.save_content_mbti(content_id, probabilities)
                            logger.info(f"内容 {content_id} MBTI评分完成并保存")
                    
                    all_results.extend(batch_results)
                else:
                    logger.error(f"第 {i//batch_size + 1} 批评分失败")
                    # 使用默认值
                    for content in batch:
                        all_results.append({
                            'id': content.get('id'),
                            'title': content.get('title', ''),
                            'E_I': 0.5,
                            'S_N': 0.5,
                            'T_F': 0.5,
                            'J_P': 0.5,
                            'from_cache': False,
                            'error': '批量评分失败'
                        })
                
                # 批次间短暂延迟，避免API限制
                if i + batch_size < len(contents_to_evaluate):
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"处理第 {i//batch_size + 1} 批时异常: {e}")
                # 使用默认值
                for content in batch:
                    all_results.append({
                        'id': content.get('id'),
                        'title': content.get('title', ''),
                        'E_I': 0.5,
                        'S_N': 0.5,
                        'T_F': 0.5,
                        'J_P': 0.5,
                        'from_cache': False,
                        'error': str(e)
                    })
        
        logger.info(f"批量评价完成: {len(all_results)}/{len(contents)} 个内容")
        
        return {
            'results': all_results,
            'total': len(contents),
            'successful': len(all_results),
            'cached': len(cached_results),
            'new_evaluated': len(all_results) - len(cached_results)
        }
    
    async def _batch_evaluate_with_llm(self, contents: List[Dict]) -> List[Dict]:
        """使用大模型批量评价多个内容的MBTI特征
        
        Args:
            contents: 内容列表，每个内容包含 id, title, content 等字段
            
        Returns:
            评价结果列表
        """
        try:
            # 构建批量内容的提示词
            batch_content = self._build_batch_content_for_llm(contents)
            
            # 使用批量提示词模板
            prompt = CONFIG["mbti"]["batch_evaluation_prompt"].format(
                contents=batch_content
            )
            
            logger.info(f"调用大模型批量评价 {len(contents)} 个内容")
            
            # 调用大模型
            response = await self._call_llm_api(prompt)
            
            if response and response.get('choices'):
                content_text = response['choices'][0].get('message', {}).get('content', '')
                
                # 无论解析是否失败，都打印完整响应
                print(f"\n🔍 大模型完整响应内容:")
                print("=" * 80)
                print(content_text)
                print("=" * 80)
                
                # 解析批量响应
                batch_results = self._parse_batch_llm_response(content_text, contents)
                
                if batch_results:
                    logger.info(f"批量评价成功: {len(batch_results)} 个结果")
                    return batch_results
                else:
                    logger.warning("批量响应解析失败")
                    return None
            else:
                logger.error(f"大模型调用失败: {response}")
                return None
                
        except Exception as e:
            logger.error(f"批量评价异常: {e}")
            return None
    
    def _build_batch_content_for_llm(self, contents: List[Dict]) -> str:
        """构建批量内容的提示词
        
        Args:
            contents: 内容列表
            
        Returns:
            格式化的批量内容字符串
        """
        batch_lines = []
        for i, content in enumerate(contents, 1):
            content_id = content.get('id', 'unknown')
            title = content.get('title', '')[:100]  # 限制标题长度
            content_text = content.get('content', '')[:500]  # 限制内容长度
            
            batch_lines.append(f"{i}. ID: {content_id}")
            batch_lines.append(f"   标题: {title}")
            batch_lines.append(f"   内容: {content_text}")
            batch_lines.append("")  # 空行分隔
        
        return "\n".join(batch_lines)
    
    def _parse_batch_llm_response(self, response_text: str, contents: List[Dict]) -> List[Dict]:
        """解析大模型的批量MBTI评分响应
        
        Args:
            response_text: 大模型返回的文本
            contents: 原始内容列表
            
        Returns:
            评价结果列表
        """
        try:
            import json
            import re
            
            # 清理响应文本，提取JSON部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # 检查是否是批量结果格式
                if 'results' in data and isinstance(data['results'], list):
                    results = []
                    for i, result in enumerate(data['results']):
                        if i < len(contents):  # 确保不超出原始内容数量
                            content = contents[i]
                            content_id = content.get('id')
                            
                            # 提取MBTI数据
                            mbti_data = result.get('mbti_probabilities', result.get('mbti', result))
                            
                            if mbti_data and isinstance(mbti_data, dict):
                                # 转换为标准格式
                                probabilities = {}
                                for trait in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']:
                                    if trait in mbti_data:
                                        probabilities[trait] = float(mbti_data[trait])
                                    else:
                                        probabilities[trait] = 0.5
                                
                                # 验证概率
                                if self._validate_probabilities(probabilities):
                                    results.append({
                                        'id': content_id,
                                        'title': content.get('title', ''),
                                        'E_I': probabilities.get('E', 0.5),
                                        'S_N': probabilities.get('S', 0.5),
                                        'T_F': probabilities.get('T', 0.5),
                                        'J_P': probabilities.get('J', 0.5),
                                        'from_cache': False,
                                        'success': True
                                    })
                                else:
                                    results.append({
                                        'id': content_id,
                                        'title': content.get('title', ''),
                                        'E_I': 0.5,
                                        'S_N': 0.5,
                                        'T_F': 0.5,
                                        'J_P': 0.5,
                                        'from_cache': False,
                                        'success': False,
                                        'error': '概率验证失败'
                                    })
                            else:
                                results.append({
                                    'id': content_id,
                                    'title': content.get('title', ''),
                                    'E_I': 0.5,
                                    'S_N': 0.5,
                                    'T_F': 0.5,
                                    'J_P': 0.5,
                                    'from_cache': False,
                                    'success': False,
                                    'error': 'MBTI数据格式错误'
                                })
                    
                    return results
            
            logger.warning(f"无法解析批量响应: {response_text}")
            return None
            
        except Exception as e:
            logger.error(f"解析批量响应异常: {e}")
            return None
    
    async def update_user_mbti_profile(self, user_id: int, force_update: bool = False,
                                     analyze_last_n: int = 100) -> Dict[str, Any]:
        """更新用户MBTI档案"""
        logger.info(f"开始更新用户 {user_id} 的MBTI档案")
        
        # 获取用户当前档案
        current_profile = db_service.get_user_profile(user_id)
        
        # 检查是否需要更新
        if not force_update and current_profile:
            threshold = CONFIG["behavior"]["mbti_update"]["behavior_threshold"]
            if current_profile.behaviors_since_last_update < threshold:
                logger.info(f"用户 {user_id} 行为数量({current_profile.behaviors_since_last_update})未达到更新阈值({threshold})")
                return {
                    "updated": False,
                    "reason": "行为数量未达到更新阈值",
                    "current_profile": current_profile.to_dict() if current_profile else None
                }
        
        # 如果用户没有MBTI类型但行为数达到阈值，强制更新
        if current_profile and not current_profile.mbti_type:
            threshold = CONFIG["behavior"]["mbti_update"]["behavior_threshold"]
            if current_profile.behaviors_since_last_update >= threshold:
                logger.info(f"用户 {user_id} 行为数达到{threshold}但MBTI未建立，强制更新")
                force_update = True
        
        # 获取用户最近的行为记录（每次更新都获取最新的行为）
        recent_behaviors = db_service.get_recent_user_behaviors_for_analysis(user_id, analyze_last_n)
        
        min_behaviors = CONFIG["behavior"]["mbti_update"]["min_behaviors_for_analysis"]
        if len(recent_behaviors) < min_behaviors:
            logger.warning(f"用户 {user_id} 行为数量({len(recent_behaviors)})不足，最少需要{min_behaviors}个行为")
            return {
                "updated": False,
                "reason": f"行为数量不足，需要至少{min_behaviors}个行为",
                "current_behaviors": len(recent_behaviors)
            }
        
        logger.info(f"用户 {user_id} 有 {len(recent_behaviors)} 个行为记录，开始分析")
        
        # 获取涉及的内容ID和权重
        content_weights = {}
        for behavior in recent_behaviors:
            content_id = behavior.content_id
            weight = behavior.weight
            
            if content_id not in content_weights:
                content_weights[content_id] = 0
            content_weights[content_id] += weight
        
        # 获取内容的MBTI评价
        content_ids = list(content_weights.keys())
        logger.info(f"分析用户 {user_id} 的 {len(content_ids)} 个不同内容")
        
        # 批量获取或评价内容MBTI
        content_mbti_data = {}
        evaluated_count = 0
        existing_count = 0
        
        for content_id in content_ids:
            existing_mbti = db_service.get_content_mbti(content_id)
            if existing_mbti:
                content_mbti_data[content_id] = existing_mbti.to_dict()["probabilities"]
                existing_count += 1
            else:
                # 如果没有评价，先评价这个内容
                try:
                    logger.info(f"内容 {content_id} 没有MBTI评分，开始评分...")
                    probabilities = await self.evaluate_content_by_id(content_id)
                    content_mbti_data[content_id] = probabilities
                    evaluated_count += 1
                    logger.info(f"内容 {content_id} MBTI评分完成")
                except Exception as e:
                    logger.error(f"评价内容 {content_id} 失败: {e}")
                    # 使用默认值
                    content_mbti_data[content_id] = {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, 
                                                   "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
        
        logger.info(f"内容MBTI分析完成: {existing_count} 个已有评分, {evaluated_count} 个新评分")
        
        # 计算加权平均MBTI概率
        weighted_probs = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
        total_weight = 0
        
        for content_id, weight in content_weights.items():
            content_probs = content_mbti_data.get(content_id, {})
            for trait in weighted_probs:
                weighted_probs[trait] += content_probs.get(trait, 0.5) * weight
            total_weight += weight
        
        # 归一化
        if total_weight > 0:
            for trait in weighted_probs:
                weighted_probs[trait] /= total_weight
        
        # 与历史MBTI评分融合
        final_probs = weighted_probs.copy()
        if current_profile and current_profile.mbti_type:
            # 如果用户已有MBTI类型，新旧MBTI做平均
            logger.info(f"用户 {user_id} 已有MBTI类型 {current_profile.mbti_type}，进行新旧MBTI平均")
            
            current_probs = {
                "E": current_profile.E, "I": current_profile.I,
                "S": current_profile.S, "N": current_profile.N,
                "T": current_profile.T, "F": current_profile.F,
                "J": current_profile.J, "P": current_profile.P
            }
            
            # 新旧MBTI各占50%权重
            for trait in final_probs:
                final_probs[trait] = (current_probs.get(trait, 0.5) + weighted_probs[trait]) / 2
        else:
            # 如果用户没有MBTI类型，直接使用新计算的MBTI
            logger.info(f"用户 {user_id} 没有MBTI类型，使用新计算的MBTI")
            final_probs = weighted_probs.copy()
        
        # 归一化最终概率
        final_probs = self._normalize_probabilities(final_probs)
        
        # 更新数据库
        updated_profile = db_service.update_user_profile(
            user_id=user_id,
            probabilities=final_probs,
            total_behaviors=len(recent_behaviors)
        )
        
        logger.info(f"用户 {user_id} MBTI档案更新完成: {updated_profile.mbti_type}")
        
        return {
            "updated": True,
            "user_id": user_id,
            "old_mbti_type": current_profile.mbti_type if current_profile else None,
            "new_mbti_type": updated_profile.mbti_type,
            "behaviors_analyzed": len(recent_behaviors),
            "contents_analyzed": len(content_ids),
            "probability_changes": self._calculate_probability_changes(current_profile, final_probs) if current_profile else None,
            "update_time": updated_profile.last_updated.isoformat(),
            "new_profile": updated_profile.to_dict()
        }
    
    def _calculate_probability_changes(self, old_profile, new_probs: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """计算概率变化"""
        if not old_profile:
            return {}
        
        old_probs = {
            "E": old_profile.E, "I": old_profile.I,
            "S": old_profile.S, "N": old_profile.N,
            "T": old_profile.T, "F": old_profile.F,
            "J": old_profile.J, "P": old_profile.P
        }
        
        changes = {}
        for trait in new_probs:
            old_val = old_probs.get(trait, 0.5)
            new_val = new_probs[trait]
            changes[trait] = {
                "old": round(old_val, 3),
                "new": round(new_val, 3),
                "change": round(new_val - old_val, 3)
            }
        
        return changes
    
    async def _evaluate_content_with_llm(self, title: str, content: str) -> Optional[Dict[str, float]]:
        """使用LLM评价单个内容的MBTI特征
        
        Args:
            title: 内容标题
            content: 内容文本
            
        Returns:
            MBTI概率字典，失败时返回None
        """
        try:
            # 构建单个内容的提示词
            single_content = f"ID: {title}\n标题: {title}\n内容: {content[:1000]}"
            
            # 使用批量提示词模板，但只传入一个内容
            prompt = CONFIG["mbti"]["batch_evaluation_prompt"].format(
                contents=single_content
            )
            
            logger.info(f"调用LLM评价内容: {title[:30]}...")
            
            # 调用LLM
            response = await self._call_llm_api(prompt)
            
            # 打印调试信息
            print(f"🔍 DEBUG: LLM原始响应: {response}")
            
            if response and response.get('choices'):
                content_text = response['choices'][0].get('message', {}).get('content', '')
                print(f"🔍 DEBUG: LLM内容文本: {content_text}")
                
                # 解析LLM响应
                probabilities = self._parse_llm_response(content_text)
                print(f"🔍 DEBUG: 解析后的概率: {probabilities}")
                
                if probabilities:
                    logger.info(f"LLM评价成功: {probabilities}")
                    return probabilities
                else:
                    logger.warning(f"LLM响应解析失败: {content_text}")
                    return None
            else:
                logger.error(f"LLM调用失败或响应格式错误: {response}")
                return None
                
        except Exception as e:
            logger.error(f"LLM评价异常: {e}")
            return None
    
    async def ensure_content_mbti_evaluated(self, content_id: int) -> bool:
        """确保内容已进行MBTI评分，如果没有则进行评分"""
        try:
            # 检查内容是否已经有MBTI评分
            existing_mbti = db_service.get_content_mbti(content_id)
            if existing_mbti:
                logger.info(f"内容 {content_id} 已有MBTI评分，跳过")
                return True
            
            # 如果没有评分，进行评分
            logger.info(f"内容 {content_id} 没有MBTI评分，开始评分")
            probabilities = await self.evaluate_content_by_id(content_id)
            
            # 保存到数据库
            db_service.save_content_mbti(content_id, probabilities)
            logger.info(f"内容 {content_id} MBTI评分完成并保存")
            return True
            
        except Exception as e:
            logger.error(f"确保内容 {content_id} MBTI评分失败: {e}")
            return False
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, float]]:
        """解析LLM的MBTI评分响应
        
        Args:
            response_text: LLM返回的文本
            
        Returns:
            MBTI概率字典，失败时返回None
        """
        try:
            # 尝试直接解析JSON
            import json
            import re
            
            # 清理响应文本，提取JSON部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # 检查是否是批量结果格式
                if 'results' in data and isinstance(data['results'], list) and len(data['results']) > 0:
                    # 取第一个结果
                    first_result = data['results'][0]
                    if 'mbti' in first_result:
                        mbti_data = first_result['mbti']
                    elif 'mbti_probabilities' in first_result:
                        mbti_data = first_result['mbti_probabilities']
                    else:
                        # 直接包含MBTI数据
                        mbti_data = first_result
                    
                    # 转换为标准格式
                    probabilities = {}
                    for trait in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']:
                        if trait in mbti_data:
                            probabilities[trait] = float(mbti_data[trait])
                        else:
                            probabilities[trait] = 0.5
                    
                    # 验证概率
                    if self._validate_probabilities(probabilities):
                        return probabilities
                
                # 如果不是批量格式，尝试直接解析
                elif all(trait in data for trait in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']):
                    probabilities = {trait: float(data[trait]) for trait in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']}
                    if self._validate_probabilities(probabilities):
                        return probabilities
            
            logger.warning(f"无法解析LLM响应: {response_text}")
            return None
            
        except Exception as e:
            logger.error(f"解析LLM响应异常: {e}")
            return None
    
    def _validate_probabilities(self, probabilities: Dict[str, float]) -> bool:
        """验证MBTI概率的有效性
        
        Args:
            probabilities: MBTI概率字典
            
        Returns:
            是否有效
        """
        try:
            # 检查是否包含所有必需的维度
            required_traits = ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']
            if not all(trait in probabilities for trait in required_traits):
                return False
            
            # 检查概率值是否在0-1之间
            for trait in required_traits:
                if not (0 <= probabilities[trait] <= 1):
                    return False
            
            # 检查对立维度概率和是否为1
            pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
            for trait1, trait2 in pairs:
                if abs(probabilities[trait1] + probabilities[trait2] - 1.0) > 0.01:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证概率异常: {e}")
            return False
    
    async def update_content_mbti_when_users_reach_50(self, content_id: int, force_update: bool = False) -> Dict[str, Any]:
        """当帖子的操作用户数量达到50个时，更新帖子的MBTI
        
        Args:
            content_id: 内容ID
            force_update: 是否强制更新
            
        Returns:
            更新结果字典
        """
        logger.info(f"检查内容 {content_id} 是否需要更新MBTI（操作用户数量达到50）")
        
        try:
            # 获取内容的操作用户数量
            operation_users = db_service.get_content_operation_users(content_id)
            user_count = len(operation_users)
            
            # 检查操作用户数量是否达到50
            if not force_update and user_count < 50:
                logger.info(f"内容 {content_id} 操作用户数量({user_count})未达到50，跳过更新")
                return {
                    "updated": False,
                    "reason": f"操作用户数量({user_count})未达到50",
                    "content_id": content_id
                }
            
            logger.info(f"内容 {content_id} 操作用户数量达到{user_count}，开始更新MBTI")
            
            # 步骤1: 计算操作用户的平均MBTI
            user_mbti_list = []
            for user_id in operation_users:
                user_profile = db_service.get_user_profile(user_id)
                if user_profile and user_profile.mbti_type:
                    user_mbti = {
                        "E": user_profile.E, "I": user_profile.I,
                        "S": user_profile.S, "N": user_profile.N,
                        "T": user_profile.T, "F": user_profile.F,
                        "J": user_profile.J, "P": user_profile.P
                    }
                    user_mbti_list.append(user_mbti)
            
            if not user_mbti_list:
                logger.warning(f"内容 {content_id} 的操作用户都没有MBTI档案")
                return {
                    "updated": False,
                    "reason": "操作用户都没有MBTI档案",
                    "content_id": content_id
                }
            
            # 计算用户平均MBTI
            avg_user_mbti = self._calculate_average_mbti(user_mbti_list)
            logger.info(f"操作用户平均MBTI: {avg_user_mbti}")
            
            # 步骤2: 获取内容当前的MBTI评分
            current_content_mbti = db_service.get_content_mbti(content_id)
            if not current_content_mbti:
                logger.warning(f"内容 {content_id} 没有当前MBTI评分")
                return {
                    "updated": False,
                    "reason": "内容没有当前MBTI评分",
                    "content_id": content_id
                }
            
            current_content_probs = {
                "E": current_content_mbti.E, "I": current_content_mbti.I,
                "S": current_content_mbti.S, "N": current_content_mbti.N,
                "T": current_content_mbti.T, "F": current_content_mbti.F,
                "J": current_content_mbti.J, "P": current_content_mbti.P
            }
            
            # 步骤3: 计算新的内容MBTI（用户平均MBTI和内容旧MBTI的平均值）
            new_content_mbti = {}
            for trait in ["E", "I", "S", "N", "T", "F", "J", "P"]:
                user_avg = avg_user_mbti.get(trait, 0.5)
                content_old = current_content_probs.get(trait, 0.5)
                # 新旧各占50%权重
                new_content_mbti[trait] = (user_avg + content_old) / 2
            
            # 归一化新内容MBTI
            new_content_mbti = self._normalize_probabilities(new_content_mbti)
            
            # 步骤4: 更新内容MBTI
            updated_content = db_service.update_content_mbti(
                content_id=content_id,
                probabilities=new_content_mbti
            )
            
            logger.info(f"内容 {content_id} MBTI更新完成")
            
            return {
                "updated": True,
                "content_id": content_id,
                "user_count": user_count,
                "old_content_mbti": current_content_probs,
                "new_content_mbti": new_content_mbti,
                "avg_user_mbti": avg_user_mbti,
                "total_users": len(operation_users),
                "update_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"更新内容 {content_id} MBTI失败: {e}")
            return {
                "updated": False,
                "reason": str(e),
                "content_id": content_id
            }
    
    async def update_user_mbti_when_posts_reach_50_multiple(self, user_id: int, force_update: bool = False) -> Dict[str, Any]:
        """当用户操作的帖子数量达到50倍数时，更新用户的MBTI
        
        Args:
            user_id: 用户ID
            force_update: 是否强制更新
            
        Returns:
            更新结果字典
        """
        logger.info(f"检查用户 {user_id} 是否需要更新MBTI（操作帖子数量达到50倍数）")
        
        try:
            # 获取用户操作的帖子数量
            user_operation_posts = db_service.get_user_operation_posts(user_id)
            post_count = len(user_operation_posts)
            
            # 检查帖子数量是否达到50的倍数
            if not force_update and post_count % 50 != 0:
                logger.info(f"用户 {user_id} 操作帖子数量({post_count})未达到50的倍数，跳过更新")
                return {
                    "updated": False,
                    "reason": f"操作帖子数量({post_count})未达到50的倍数",
                    "current_posts": post_count
                }
            
            logger.info(f"用户 {user_id} 操作帖子数量达到{post_count}（50的倍数），开始更新MBTI")
            
            # 步骤1: 获取用户当前MBTI档案
            current_profile = db_service.get_user_profile(user_id)
            if not current_profile:
                logger.warning(f"用户 {user_id} 没有MBTI档案")
                return {
                    "updated": False,
                    "reason": "用户没有MBTI档案",
                    "user_id": user_id
                }
            
            current_user_probs = {
                "E": current_profile.E, "I": current_profile.I,
                "S": current_profile.S, "N": current_profile.N,
                "T": current_profile.T, "F": current_profile.F,
                "J": current_profile.J, "P": current_profile.P
            }
            
            # 步骤2: 计算用户操作帖子的平均MBTI
            post_mbti_list = []
            for post_id in user_operation_posts:
                post_mbti = db_service.get_content_mbti(post_id)
                if post_mbti:
                    post_mbti_data = {
                        "E": post_mbti.E, "I": post_mbti.I,
                        "S": post_mbti.S, "N": post_mbti.N,
                        "T": post_mbti.T, "F": post_mbti.F,
                        "J": post_mbti.J, "P": post_mbti.P
                    }
                    post_mbti_list.append(post_mbti_data)
            
            if not post_mbti_list:
                logger.warning(f"用户 {user_id} 操作的帖子都没有MBTI评分")
                return {
                    "updated": False,
                    "reason": "操作的帖子都没有MBTI评分",
                    "user_id": user_id
                }
            
            # 计算帖子平均MBTI
            avg_post_mbti = self._calculate_average_mbti(post_mbti_list)
            logger.info(f"用户操作帖子平均MBTI: {avg_post_mbti}")
            
            # 步骤3: 计算新的用户MBTI（当前用户MBTI和帖子平均MBTI的平均值）
            new_user_mbti = {}
            for trait in ["E", "I", "S", "N", "T", "F", "J", "P"]:
                user_current = current_user_probs.get(trait, 0.5)
                post_avg = avg_post_mbti.get(trait, 0.5)
                # 新旧各占50%权重
                new_user_mbti[trait] = (user_current + post_avg) / 2
            
            # 归一化新用户MBTI
            new_user_mbti = self._normalize_probabilities(new_user_mbti)
            
            # 步骤4: 更新用户MBTI档案
            updated_profile = db_service.update_user_profile(
                user_id=user_id,
                probabilities=new_user_mbti,
                total_behaviors=current_profile.behaviors_since_last_update
            )
            
            logger.info(f"用户 {user_id} MBTI更新完成: {updated_profile.mbti_type}")
            
            return {
                "updated": True,
                "user_id": user_id,
                "post_count": post_count,
                "old_mbti_type": current_profile.mbti_type,
                "new_mbti_type": updated_profile.mbti_type,
                "old_probabilities": current_user_probs,
                "new_probabilities": new_user_mbti,
                "avg_post_mbti": avg_post_mbti,
                "update_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"更新用户 {user_id} MBTI失败: {e}")
            return {
                "updated": False,
                "reason": str(e),
                "user_id": user_id
            }
    
    def _calculate_average_mbti(self, mbti_list: List[Dict[str, float]]) -> Dict[str, float]:
        """计算多个MBTI概率的平均值"""
        if not mbti_list:
            return {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, 
                   "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
        
        avg_mbti = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
        
        for mbti in mbti_list:
            for trait in avg_mbti:
                avg_mbti[trait] += mbti.get(trait, 0.5)
        
        # 计算平均值
        count = len(mbti_list)
        for trait in avg_mbti:
            avg_mbti[trait] /= count
        
        # 归一化
        return self._normalize_probabilities(avg_mbti)

# 全局MBTI评价服务实例
mbti_service = MBTIEvaluationService()
