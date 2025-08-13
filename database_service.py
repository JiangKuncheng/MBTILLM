# -*- coding: utf-8 -*-
"""
数据库服务层
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from models import (
    UserProfile, UserBehavior, ContentMBTI, RecommendationLog,
    create_database_engine, create_tables, get_session_factory,
    get_mbti_type_from_probabilities, calculate_confidence_scores,
    normalize_mbti_probabilities
)
from new_config import CONFIG

logger = logging.getLogger(__name__)

class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = f"sqlite:///{CONFIG['database']['sqlite_path']}"
        
        self.engine = create_database_engine(database_url)
        create_tables(self.engine)
        self.SessionFactory = get_session_factory(self.engine)
        
        logger.info("数据库服务初始化完成")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionFactory()
    
    # =============================================================================
    # 用户档案管理
    # =============================================================================
    
    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户MBTI档案"""
        with self.get_session() as session:
            return session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def create_user_profile(self, user_id: int, **kwargs) -> UserProfile:
        """创建用户MBTI档案"""
        with self.get_session() as session:
            # 检查是否已存在
            existing = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if existing:
                return existing
            
            # 创建新档案
            profile = UserProfile(user_id=user_id, **kwargs)
            session.add(profile)
            session.commit()
            session.refresh(profile)
            
            logger.info(f"创建用户 {user_id} 的MBTI档案")
            return profile
    
    def update_user_profile(self, user_id: int, probabilities: Dict[str, float], 
                          total_behaviors: int = None) -> UserProfile:
        """更新用户MBTI档案"""
        with self.get_session() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                # 如果不存在，创建新档案
                profile = UserProfile(user_id=user_id)
                session.add(profile)
            
            # 标准化概率
            normalized_probs = normalize_mbti_probabilities(probabilities)
            
            # 更新概率值
            profile.E = normalized_probs.get("E", 0.5)
            profile.I = normalized_probs.get("I", 0.5)
            profile.S = normalized_probs.get("S", 0.5)
            profile.N = normalized_probs.get("N", 0.5)
            profile.T = normalized_probs.get("T", 0.5)
            profile.F = normalized_probs.get("F", 0.5)
            profile.J = normalized_probs.get("J", 0.5)
            profile.P = normalized_probs.get("P", 0.5)
            
            # 更新推导的MBTI类型
            profile.mbti_type = get_mbti_type_from_probabilities(normalized_probs)
            
            # 更新置信度
            confidence = calculate_confidence_scores(normalized_probs)
            profile.confidence_E_I = confidence["E_I"]
            profile.confidence_S_N = confidence["S_N"]
            profile.confidence_T_F = confidence["T_F"]
            profile.confidence_J_P = confidence["J_P"]
            
            # 更新统计信息
            if total_behaviors is not None:
                profile.total_behaviors_analyzed = total_behaviors
            profile.behaviors_since_last_update = 0  # 重置计数器
            profile.last_updated = datetime.utcnow()
            
            session.commit()
            session.refresh(profile)
            
            logger.info(f"更新用户 {user_id} 的MBTI档案: {profile.mbti_type}")
            return profile
    
    def increment_behavior_count(self, user_id: int) -> int:
        """增加用户行为计数器"""
        with self.get_session() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                # 创建默认档案
                profile = UserProfile(user_id=user_id, behaviors_since_last_update=1)
                session.add(profile)
            else:
                profile.behaviors_since_last_update += 1
            
            session.commit()
            return profile.behaviors_since_last_update
    
    # =============================================================================
    # 用户行为管理
    # =============================================================================
    
    def record_user_behavior(self, user_id: int, content_id: int, action: str,
                           weight: float = None, source: str = "unknown",
                           session_id: str = None, extra_data: Dict = None,
                           timestamp: datetime = None) -> UserBehavior:
        """记录用户行为"""
        with self.get_session() as session:
            # 设置默认权重
            if weight is None:
                weight = CONFIG["behavior"]["weights"].get(action, 0.1)
            
            # 创建行为记录
            behavior = UserBehavior(
                user_id=user_id,
                content_id=content_id,
                action=action,
                weight=weight,
                source=source,
                session_id=session_id,
                extra_data=extra_data,
                timestamp=timestamp or datetime.utcnow()
            )
            
            session.add(behavior)
            session.commit()
            session.refresh(behavior)
            
            logger.info(f"记录用户 {user_id} 对内容 {content_id} 的 {action} 行为")
            return behavior
    
    def get_user_behaviors(self, user_id: int, action: str = None, 
                          start_date: datetime = None, end_date: datetime = None,
                          limit: int = 100, offset: int = 0) -> Tuple[List[UserBehavior], int]:
        """获取用户行为历史"""
        with self.get_session() as session:
            query = session.query(UserBehavior).filter(UserBehavior.user_id == user_id)
            
            # 添加过滤条件
            if action:
                query = query.filter(UserBehavior.action == action)
            if start_date:
                query = query.filter(UserBehavior.timestamp >= start_date)
            if end_date:
                query = query.filter(UserBehavior.timestamp <= end_date)
            
            # 获取总数
            total_count = query.count()
            
            # 分页查询
            behaviors = query.order_by(desc(UserBehavior.timestamp)).offset(offset).limit(limit).all()
            
            return behaviors, total_count
    
    def get_user_behavior_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取用户行为统计"""
        with self.get_session() as session:
            # 计算时间范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 总行为数
            total_behaviors = session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id
            ).count()
            
            # 最近N天行为数
            recent_behaviors = session.query(UserBehavior).filter(
                and_(
                    UserBehavior.user_id == user_id,
                    UserBehavior.timestamp >= start_date
                )
            ).count()
            
            # 行为类型分布
            action_stats = session.query(
                UserBehavior.action,
                func.count(UserBehavior.id)
            ).filter(UserBehavior.user_id == user_id).group_by(UserBehavior.action).all()
            
            action_distribution = {action: count for action, count in action_stats}
            
            # 最后活动时间
            last_behavior = session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id
            ).order_by(desc(UserBehavior.timestamp)).first()
            
            last_activity = last_behavior.timestamp if last_behavior else None
            
            # 活跃程度评估
            daily_avg = recent_behaviors / days if days > 0 else 0
            if daily_avg >= 5:
                activity_level = "高度活跃"
            elif daily_avg >= 2:
                activity_level = "中度活跃"
            elif daily_avg >= 0.5:
                activity_level = "低度活跃"
            else:
                activity_level = "不活跃"
            
            # 获取用户档案中的行为计数
            profile = self.get_user_profile(user_id)
            behaviors_since_update = profile.behaviors_since_last_update if profile else 0
            
            return {
                "total_behaviors": total_behaviors,
                f"last_{days}_days": recent_behaviors,
                "action_distribution": action_distribution,
                "activity_level": activity_level,
                "last_activity": last_activity.isoformat() if last_activity else None,
                "behaviors_since_last_mbti_update": behaviors_since_update,
                "daily_average": round(daily_avg, 2)
            }
    
    def get_recent_user_behaviors_for_analysis(self, user_id: int, 
                                              limit: int = 200) -> List[UserBehavior]:
        """获取用户最近的行为用于MBTI分析"""
        with self.get_session() as session:
            return session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id
            ).order_by(desc(UserBehavior.timestamp)).limit(limit).all()
    
    def get_content_behaviors(self, content_id: int, limit: int = 100) -> List[UserBehavior]:
        """获取特定内容的行为记录"""
        with self.get_session() as session:
            return session.query(UserBehavior).filter(
                UserBehavior.content_id == content_id
            ).order_by(desc(UserBehavior.timestamp)).limit(limit).all()
    
    # =============================================================================
    # 内容MBTI管理
    # =============================================================================
    
    def get_content_mbti(self, content_id: int) -> Optional[ContentMBTI]:
        """获取内容MBTI评价"""
        with self.get_session() as session:
            return session.query(ContentMBTI).filter(ContentMBTI.content_id == content_id).first()
    
    def save_content_mbti(self, content_id: int, probabilities: Dict[str, float],
                         content_title: str = None, content_type: str = None,
                         quality_score: float = 0.5) -> ContentMBTI:
        """保存内容MBTI评价"""
        with self.get_session() as session:
            # 检查是否已存在
            existing = session.query(ContentMBTI).filter(ContentMBTI.content_id == content_id).first()
            if existing:
                return existing
            
            # 标准化概率
            normalized_probs = normalize_mbti_probabilities(probabilities)
            
            # 创建新记录
            content_mbti = ContentMBTI(
                content_id=content_id,
                E=normalized_probs.get("E", 0.5),
                I=normalized_probs.get("I", 0.5),
                S=normalized_probs.get("S", 0.5),
                N=normalized_probs.get("N", 0.5),
                T=normalized_probs.get("T", 0.5),
                F=normalized_probs.get("F", 0.5),
                J=normalized_probs.get("J", 0.5),
                P=normalized_probs.get("P", 0.5)
            )
            
            session.add(content_mbti)
            session.commit()
            session.refresh(content_mbti)
            
            logger.info(f"保存内容 {content_id} 的MBTI评价")
            return content_mbti
    
    def get_contents_for_recommendation(self, content_type: str = None,
                                      fresh_days: int = 30,
                                      exclude_content_ids: List[int] = None,
                                      limit: int = 1000) -> List[ContentMBTI]:
        """获取用于推荐的内容列表"""
        with self.get_session() as session:
            query = session.query(ContentMBTI)
            
            # 排除已浏览内容
            if exclude_content_ids:
                query = query.filter(~ContentMBTI.content_id.in_(exclude_content_ids))
            
            # 按创建时间排序（最新的在前）
            contents = query.order_by(desc(ContentMBTI.created_at)).limit(limit).all()
            
            return contents
    
    def get_viewed_content_ids(self, user_id: int, days: int = 30) -> List[int]:
        """获取用户已浏览的内容ID列表（只考虑like行为）"""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 只考虑like行为
            viewed_ids = session.query(UserBehavior.content_id).filter(
                and_(
                    UserBehavior.user_id == user_id,
                    UserBehavior.action == 'like',  # 只考虑like行为
                    UserBehavior.timestamp >= cutoff_date
                )
            ).distinct().all()
            
            return [content_id for (content_id,) in viewed_ids]
    
    # =============================================================================
    # 推荐算法
    # =============================================================================
    
    def calculate_mbti_similarity(self, user_vector: List[float], 
                                 content_vectors: List[List[float]]) -> List[float]:
        """计算MBTI相似度"""
        if not content_vectors:
            return []
        
        user_array = np.array(user_vector).reshape(1, -1)
        content_array = np.array(content_vectors)
        
        # 计算余弦相似度
        similarities = cosine_similarity(user_array, content_array)[0]
        
        return similarities.tolist()
    
    def get_recommendations_for_user(self, user_id: int, limit: int = 50,
                                   content_type: str = None, 
                                   similarity_threshold: float = 0.5,
                                   exclude_viewed: bool = True,
                                   fresh_days: int = 30) -> Dict[str, Any]:
        """为用户生成推荐"""
        # 获取用户MBTI档案
        user_profile = self.get_user_profile(user_id)
        if not user_profile:
            # 创建默认档案
            user_profile = self.create_user_profile(user_id)
        
        # 获取用户MBTI向量
        user_vector = [
            user_profile.E, user_profile.I, user_profile.S, user_profile.N,
            user_profile.T, user_profile.F, user_profile.J, user_profile.P
        ]
        
        # 获取排除的内容ID
        exclude_content_ids = []
        if exclude_viewed:
            exclude_content_ids = self.get_viewed_content_ids(user_id, fresh_days)
        
        # 获取候选内容
        candidate_contents = self.get_contents_for_recommendation(
            content_type=content_type,
            fresh_days=fresh_days,
            exclude_content_ids=exclude_content_ids,
            limit=1000  # 获取更多候选内容用于计算
        )
        
        if not candidate_contents:
            return {
                "user_id": user_id,
                "user_mbti_type": user_profile.mbti_type,
                "user_mbti_probabilities": user_profile.to_dict()["probabilities"],
                "recommendations": [],
                "metadata": {
                    "total_candidates": 0,
                    "filtered_count": 0,
                    "avg_similarity": 0.0,
                    "generation_time": datetime.utcnow().isoformat(),
                    "algorithm_version": "v1.0"
                }
            }
        
        # 计算相似度
        content_vectors = [content.get_vector() for content in candidate_contents]
        similarities = self.calculate_mbti_similarity(user_vector, content_vectors)
        
        # 生成所有推荐（不使用阈值过滤）
        all_recommendations = []
        for i, (content, similarity) in enumerate(zip(candidate_contents, similarities)):
            all_recommendations.append({
                "content_id": content.content_id,
                "similarity_score": round(similarity, 4),
                "mbti_match_traits": self._get_matching_traits(user_profile, content),
                "rank": 0,  # 稍后设置
                "estimated_engagement": min(similarity * 0.8, 1.0)  # 使用默认质量分数
            })
        
        # 按相似度排序
        all_recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # 确保至少返回50条推荐（如果有足够的候选内容）
        min_recommendations = 50
        target_limit = max(limit, min_recommendations)
        
        # 先尝试用阈值过滤
        filtered_recommendations = [rec for rec in all_recommendations if rec["similarity_score"] >= similarity_threshold]
        
        # 如果过滤后不足50条，直接取前N条最相似的
        if len(filtered_recommendations) < min_recommendations:
            recommendations = all_recommendations[:target_limit]
            logger.info(f"阈值过滤后推荐不足{min_recommendations}条，直接返回前{len(recommendations)}条最相似的")
        else:
            recommendations = filtered_recommendations[:target_limit]
        
        # 设置排名
        for i, rec in enumerate(recommendations):
            rec["rank"] = i + 1
        
        # 计算统计信息
        avg_similarity = np.mean([rec["similarity_score"] for rec in recommendations]) if recommendations else 0.0
        
        result = {
            "user_id": user_id,
            "user_mbti_type": user_profile.mbti_type,
            "user_mbti_probabilities": user_profile.to_dict()["probabilities"],
            "recommendations": recommendations,
            "metadata": {
                "total_candidates": len(candidate_contents),
                "filtered_count": len(recommendations),
                "avg_similarity": round(avg_similarity, 4),
                "generation_time": datetime.utcnow().isoformat(),
                "algorithm_version": "v1.0",
                "cache_hit": False
            }
        }
        
        # 记录推荐日志
        self._log_recommendation(user_id, result, similarity_threshold, content_type, limit)
        
        return result
    
    def _get_matching_traits(self, user_profile: UserProfile, content: ContentMBTI) -> List[str]:
        """获取匹配的MBTI特征"""
        matching_traits = []
        
        if user_profile.E > user_profile.I and content.E > content.I:
            matching_traits.append("E")
        elif user_profile.I > user_profile.E and content.I > content.E:
            matching_traits.append("I")
            
        if user_profile.S > user_profile.N and content.S > content.N:
            matching_traits.append("S")
        elif user_profile.N > user_profile.S and content.N > content.S:
            matching_traits.append("N")
            
        if user_profile.T > user_profile.F and content.T > content.F:
            matching_traits.append("T")
        elif user_profile.F > user_profile.T and content.F > content.T:
            matching_traits.append("F")
            
        if user_profile.J > user_profile.P and content.J > content.P:
            matching_traits.append("J")
        elif user_profile.P > user_profile.J and content.P > content.J:
            matching_traits.append("P")
        
        return matching_traits
    

    
    def _log_recommendation(self, user_id: int, result: Dict[str, Any],
                          similarity_threshold: float, content_type: str, limit: int):
        """记录推荐日志"""
        with self.get_session() as session:
            log = RecommendationLog(
                user_id=user_id,
                recommended_content_ids=[rec["content_id"] for rec in result["recommendations"]],
                similarity_scores=[rec["similarity_score"] for rec in result["recommendations"]],
                limit=limit,
                content_type_filter=content_type,
                similarity_threshold=similarity_threshold,
                total_candidates=result["metadata"]["total_candidates"],
                avg_similarity=result["metadata"]["avg_similarity"],
                user_mbti_snapshot=result["user_mbti_probabilities"]
            )
            
            session.add(log)
            session.commit()
    
    # =============================================================================
    # 工具方法
    # =============================================================================
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.get_session() as session:
            user_count = session.query(UserProfile).count()
            behavior_count = session.query(UserBehavior).count()
            content_count = session.query(ContentMBTI).count()
            recommendation_count = session.query(RecommendationLog).count()
            
            return {
                "total_users": user_count,
                "total_behaviors": behavior_count,
                "total_contents": content_count,
                "total_recommendations": recommendation_count
            }

# 全局数据库服务实例
db_service = DatabaseService()
