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
        """调用LLM API进行MBTI评价（临时使用模拟数据）"""
        import random
        import json
        
        logger.info("使用模拟API响应进行测试")
        
        # 分析内容特征来生成合理的MBTI评分
        content_lower = content.lower()
        
        # 基于内容关键词的简单MBTI判断
        e_score = 0.5  # 默认中性
        s_score = 0.5
        t_score = 0.5
        j_score = 0.5
        
        # E/I 判断
        if any(word in content_lower for word in ['团队', '协作', '社交', '分享', '交流']):
            e_score = random.uniform(0.6, 0.8)
        elif any(word in content_lower for word in ['独处', '思考', '内省', '安静', '专注']):
            e_score = random.uniform(0.2, 0.4)
        else:
            e_score = random.uniform(0.4, 0.6)
            
        # S/N 判断  
        if any(word in content_lower for word in ['数据', '事实', '细节', '具体', '实际']):
            s_score = random.uniform(0.6, 0.8)
        elif any(word in content_lower for word in ['创新', '想象', '可能', '未来', '概念']):
            s_score = random.uniform(0.2, 0.4)
        else:
            s_score = random.uniform(0.4, 0.6)
            
        # T/F 判断
        if any(word in content_lower for word in ['逻辑', '分析', '理性', '效率', '数据']):
            t_score = random.uniform(0.6, 0.8)
        elif any(word in content_lower for word in ['关怀', '情感', '价值', '和谐', '他人']):
            t_score = random.uniform(0.2, 0.4)
        else:
            t_score = random.uniform(0.4, 0.6)
            
        # J/P 判断
        if any(word in content_lower for word in ['计划', '组织', '结构', '截止', '安排']):
            j_score = random.uniform(0.6, 0.8)
        elif any(word in content_lower for word in ['灵活', '适应', '变化', '开放', '自由']):
            j_score = random.uniform(0.2, 0.4)
        else:
            j_score = random.uniform(0.4, 0.6)
        
        # 确保概率和为1
        i_score = 1.0 - e_score
        n_score = 1.0 - s_score  
        f_score = 1.0 - t_score
        p_score = 1.0 - j_score
        
        # 模拟API响应格式 - 使用JSON格式以便正确解析
        mbti_json = {
            "E": round(e_score, 3), "I": round(i_score, 3), 
            "S": round(s_score, 3), "N": round(n_score, 3), 
            "T": round(t_score, 3), "F": round(f_score, 3), 
            "J": round(j_score, 3), "P": round(p_score, 3)
        }
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps(mbti_json, ensure_ascii=False)
                }
            }]
        }
        
        return mock_response
    
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
    
    async def batch_evaluate_contents(self, content_ids: List[int], 
                                    max_concurrent: int = 3) -> Dict[int, Dict[str, float]]:
        """批量评价内容MBTI特征"""
        results = {}
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def evaluate_single(content_id: int):
            async with semaphore:
                try:
                    probabilities = await self.evaluate_content_by_id(content_id)
                    results[content_id] = probabilities
                except Exception as e:
                    logger.error(f"评价内容 {content_id} 失败: {e}")
                    results[content_id] = {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, 
                                         "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
        
        # 并发执行评价
        tasks = [evaluate_single(content_id) for content_id in content_ids]
        await asyncio.gather(*tasks)
        
        logger.info(f"批量评价完成: {len(results)}/{len(content_ids)} 个内容")
        return results
    
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
        
        # 获取用户最近的行为记录
        recent_behaviors = db_service.get_recent_user_behaviors_for_analysis(user_id, analyze_last_n)
        
        min_behaviors = CONFIG["behavior"]["mbti_update"]["min_behaviors_for_analysis"]
        if len(recent_behaviors) < min_behaviors:
            logger.warning(f"用户 {user_id} 行为数量({len(recent_behaviors)})不足，最少需要{min_behaviors}个")
            return {
                "updated": False,
                "reason": f"行为数量不足，需要至少{min_behaviors}个行为",
                "current_behaviors": len(recent_behaviors)
            }
        
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
        for content_id in content_ids:
            existing_mbti = db_service.get_content_mbti(content_id)
            if existing_mbti:
                content_mbti_data[content_id] = existing_mbti.to_dict()["probabilities"]
            else:
                # 如果没有评价，先评价这个内容
                try:
                    probabilities = await self.evaluate_content_by_id(content_id)
                    content_mbti_data[content_id] = probabilities
                except Exception as e:
                    logger.error(f"评价内容 {content_id} 失败: {e}")
                    # 使用默认值
                    content_mbti_data[content_id] = {"E": 0.5, "I": 0.5, "S": 0.5, "N": 0.5, 
                                                   "T": 0.5, "F": 0.5, "J": 0.5, "P": 0.5}
        
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
        if current_profile and not force_update:
            history_weight = CONFIG["behavior"]["mbti_update"]["history_weight"]
            new_weight = CONFIG["behavior"]["mbti_update"]["new_analysis_weight"]
            
            current_probs = {
                "E": current_profile.E, "I": current_profile.I,
                "S": current_profile.S, "N": current_profile.N,
                "T": current_profile.T, "F": current_profile.F,
                "J": current_profile.J, "P": current_profile.P
            }
            
            for trait in final_probs:
                final_probs[trait] = (history_weight * current_probs.get(trait, 0.5) + 
                                    new_weight * weighted_probs[trait])
        
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

# 全局MBTI评价服务实例
mbti_service = MBTIEvaluationService()
