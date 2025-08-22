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
        """记录用户行为 - 只记录对有实际内容的内容的行为"""
        with self.get_session() as session:
            # 首先验证内容是否适合记录行为
            if not self._should_record_behavior_for_content(content_id):
                logger.warning(f"内容 {content_id} 没有实际内容，不记录用户 {user_id} 的 {action} 行为")
                # 返回一个虚拟的行为对象，但不保存到数据库
                return UserBehavior(
                    user_id=user_id,
                    content_id=content_id,
                    action=action,
                    weight=0,  # 权重为0，表示无效行为
                    source=source,
                    session_id=session_id,
                    extra_data=extra_data,
                    timestamp=timestamp or datetime.utcnow()
                )
            
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
            
            # 记录行为后，异步检查是否需要更新MBTI
            self._async_check_mbti_updates(user_id, content_id)
            
            return behavior
    
    def _should_record_behavior_for_content(self, content_id: int) -> bool:
        """检查是否应该为内容记录行为（内容是否有实际价值）"""
        # 这里可以扩展为检查数据库中的内容，或者调用搜狐接口验证
        # 暂时返回True，实际使用时可以根据需要实现
        return True
    
    def _async_check_mbti_updates(self, user_id: int, content_id: int):
        """异步检查是否需要更新MBTI（在记录用户行为后调用）"""
        try:
            # 使用线程池异步执行，避免阻塞主流程
            import threading
            import asyncio
            
            def check_updates():
                try:
                    # 创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 检查帖子MBTI更新
                    loop.run_until_complete(self._check_content_mbti_update(content_id))
                    
                    # 检查用户MBTI更新
                    loop.run_until_complete(self._check_user_mbti_update(user_id))
                    
                    loop.close()
                except Exception as e:
                    logger.error(f"异步检查MBTI更新失败: {e}")
            
            # 启动后台线程
            thread = threading.Thread(target=check_updates, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"启动异步MBTI检查失败: {e}")
    
    async def _check_content_mbti_update(self, content_id: int):
        """检查内容是否需要更新MBTI"""
        try:
            from mbti_service import mbti_service
            
            # 调用MBTI服务检查内容更新
            result = await mbti_service.update_content_mbti_when_users_reach_50(content_id)
            
            if result.get("updated"):
                logger.info(f"内容 {content_id} MBTI自动更新成功")
            else:
                logger.debug(f"内容 {content_id} 无需更新MBTI: {result.get('reason', '未知原因')}")
                
        except Exception as e:
            logger.error(f"检查内容 {content_id} MBTI更新失败: {e}")
    
    async def _check_user_mbti_update(self, user_id: int):
        """检查用户是否需要更新MBTI"""
        try:
            from mbti_service import mbti_service
            
            # 调用MBTI服务检查用户更新
            result = await mbti_service.update_user_mbti_when_posts_reach_50_multiple(user_id)
            
            if result.get("updated"):
                logger.info(f"用户 {user_id} MBTI自动更新成功")
            else:
                logger.debug(f"用户 {user_id} 无需更新MBTI: {result.get('reason', '未知原因')}")
                
        except Exception as e:
            logger.error(f"检查用户 {user_id} MBTI更新失败: {e}")
    
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
    
    def get_user_behavior_count(self, user_id: int) -> int:
        """获取用户总行为数"""
        with self.get_session() as session:
            return session.query(UserBehavior).filter(UserBehavior.user_id == user_id).count()
    
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
                title=content_title,
                content_type=content_type or "article",
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
            
            # 如果数据库中的内容不足，从搜狐接口获取更多内容
            if len(contents) < limit:
                logger.info(f"数据库内容不足{limit}条，从搜狐接口获取更多内容")
                try:
                    # 异步获取搜狐内容（这里需要调用者处理异步）
                    # 暂时返回数据库中的内容，异步获取在外部处理
                    pass
                except Exception as e:
                    logger.error(f"从搜狐接口获取内容失败: {e}")
            
            return contents
    
    async def get_sohu_contents_for_recommendation(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """从搜狐接口获取内容用于推荐 - 只返回有实际内容的内容"""
        try:
            from sohu_client import sohu_client
            
            # 优化分页策略：增加每页数量，减少API调用次数
            page_size = 50  # 增加到每页50条，减少API调用
            target_limit = max(limit, 40)  # 确保至少获取40条
            # 计算需要的页数，并增加一些缓冲页以确保能获取足够的内容
            pages_needed = (target_limit + page_size - 1) // page_size
            # 增加缓冲页，确保能获取足够的内容
            buffer_pages = max(2, pages_needed // 2)  # 至少增加2页缓冲
            total_pages = pages_needed + buffer_pages
            
            all_contents = []
            valid_contents = []
            
            async with sohu_client as client:
                for page in range(1, total_pages + 1):
                    try:
                        # 获取图文列表，aiRec=false确保每次结果不同
                        result = await client.get_article_list(
                            page_num=page,
                            page_size=page_size,
                            state="OnShelf",  # 只获取上架的内容
                            site_id=11  # 默认站点ID
                        )
                        
                        if result.get("code") == 200 and "data" in result:
                            # 处理不同的数据结构
                            data = result["data"]
                            if isinstance(data, list):
                                articles = data
                            elif isinstance(data, dict):
                                articles = data.get("data", [])
                                if not articles and "list" in data:
                                    articles = data.get("list", [])
                            else:
                                articles = []
                            
                            all_contents.extend(articles)
                            
                            # 筛选有实际内容的内容
                            for article in articles:
                                if self._is_valid_content_for_recommendation(article):
                                    valid_contents.append(article)
                                    # 如果已经获取足够的有内容的内容，停止
                                    if len(valid_contents) >= target_limit:
                                        break
                            
                            # 如果已经获取足够的有内容的内容，停止
                            if len(valid_contents) >= target_limit:
                                break
                        else:
                            logger.warning(f"获取第{page}页内容失败: {result.get('msg')}")
                            
                    except Exception as e:
                        logger.error(f"获取第{page}页内容异常: {e}")
                        continue
            
            logger.info(f"从搜狐接口获取了{len(all_contents)}条内容，其中{len(valid_contents)}条有实际内容，目标获取{target_limit}条，实际获取{len(valid_contents)}条")
            
            # 返回筛选后的有效内容，优先返回更多内容
            return valid_contents[:target_limit]
            
        except Exception as e:
            logger.error(f"从搜狐接口获取内容失败: {e}")
            return []
    
    def _is_valid_content_for_recommendation(self, content: Dict[str, Any]) -> bool:
        """检查内容是否适合推荐（有实际内容）"""
        # 检查是否有标题
        if not content.get('title'):
            return False
        
        # 检查是否有封面图片
        if not content.get('coverImage') and not content.get('coverUrl'):
            return False
        
        # 检查内容状态
        if content.get('state') != 'OnShelf':
            return False
        
        if content.get('auditState') != 'Pass':
            return False
        
        # 检查是否有实际内容（文字内容、图片、或标题+封面的组合）
        has_content = (
            content.get('content') or  # 有文字内容
            content.get('images') or   # 有图片列表
            (content.get('title') and (content.get('coverImage') or content.get('coverUrl')))  # 有标题+封面
        )
        
        if not has_content:
            logger.debug(f"内容 {content.get('id')} 没有实际内容，跳过推荐")
            return False
        
        return True
    
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
    
    def get_recommendations_for_user(self, user_id: int, limit: int = 10, offset: int = 0,
                                   content_type: str = None, similarity_threshold: float = 0.5,
                                   exclude_viewed: bool = True, fresh_days: int = 30) -> Dict[str, Any]:
        """获取用户个性化推荐 - 直接取10条评分，评分后根据相似度排序
        
        Args:
            user_id: 用户ID
            limit: 推荐数量（默认10条）
            content_type: 内容类型
            similarity_threshold: 相似度阈值
            exclude_viewed: 是否排除已浏览内容
            fresh_days: 内容新鲜度天数
            
        Returns:
            推荐结果字典
        """
        try:
            # 获取用户MBTI档案
            user_profile = self.get_user_profile(user_id)
            if not user_profile or not user_profile.mbti_type:
                logger.info(f"用户 {user_id} 没有MBTI档案，使用随机推荐")
                return self._get_random_recommendations(limit, content_type, fresh_days)
            
            # 获取用户MBTI向量
            user_vector = [
                user_profile.E, user_profile.S, user_profile.T, user_profile.J
            ]
            
            logger.info(f"用户 {user_id} MBTI: {user_profile.mbti_type}, 向量: {user_vector}")
            
            # 从数据库获取已有MBTI评分的内容
            candidate_contents = self.get_contents_for_recommendation(limit=limit)
            
            if not candidate_contents:
                logger.warning("无法获取候选内容，使用随机推荐")
                return self._get_random_recommendations(limit, content_type, fresh_days)
            
            # 过滤有效内容
            valid_candidate_contents = []
            for content in candidate_contents:
                if hasattr(content, 'content_id') and content.content_id:
                    valid_candidate_contents.append({
                        'id': content.content_id,
                        'title': getattr(content, 'title', ''),
                        'content': getattr(content, 'content', '')
                    })
            
            if not valid_candidate_contents:
                logger.warning("没有有效内容，使用随机推荐")
                return self._get_random_recommendations(limit, content_type, fresh_days)
            
            # 确保有足够的内容进行评分
            target_contents = valid_candidate_contents[:max(limit, 10)]
            
            # 对内容进行MBTI评分（如果还没有评分）
            contents_for_scoring = []
            for content in target_contents:
                content_id = content.get('id')
                if not self.get_content_mbti(content_id):
                    contents_for_scoring.append({
                        'id': content_id,
                        'title': content.get('title', ''),
                        'content': content.get('content', '')
                    })
            
            # 如果有内容需要评分，触发评分
            if contents_for_scoring:
                logger.info(f"需要评分 {len(contents_for_scoring)} 条内容")
                # 这里会触发异步评分，但推荐接口立即返回
                # 实际评分在后台进行
            
            # 获取所有内容的MBTI评分（包括已有的和新评分的）
            scored_contents = []
            for content in target_contents:
                content_id = content.get('id')
                content_mbti = self.get_content_mbti(content_id)
                
                if content_mbti:
                    # 计算相似度
                    content_vector = [
                        content_mbti.E, content_mbti.S, content_mbti.T, content_mbti.J
                    ]
                    similarity = self.calculate_mbti_similarity([user_vector], [content_vector])[0]
                    
                    scored_contents.append({
                        'content_id': content_id,
                        'title': content.get('title', ''),
                        'similarity_score': similarity,
                        'mbti_vector': content_vector
                    })
                else:
                    # 如果没有MBTI评分，使用默认相似度
                    scored_contents.append({
                        'content_id': content_id,
                        'title': content.get('title', ''),
                        'similarity_score': 0.5,
                        'mbti_vector': [0.5, 0.5, 0.5, 0.5]
                    })
            
            # 按相似度排序
            scored_contents.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # 应用分页
            start_index = offset
            end_index = offset + limit
            top_recommendations = scored_contents[start_index:end_index]
            
            # 构建推荐结果
            recommendations = []
            for item in top_recommendations:
                recommendations.append({
                    'content_id': item['content_id'],
                    'title': item['title'],
                    'similarity_score': round(item['similarity_score'], 4),
                    'mbti_vector': item['mbti_vector']
                })
            
            # 计算统计信息
            if recommendations:
                similarities = [r['similarity_score'] for r in recommendations]
                avg_similarity = sum(similarities) / len(similarities)
                max_similarity = max(similarities)
                min_similarity = min(similarities)
            else:
                avg_similarity = max_similarity = min_similarity = 0.0
            
            return {
                'recommendations': recommendations,
                'user_mbti': {
                    'type': user_profile.mbti_type,
                    'vector': user_vector
                },
                'similarity_stats': {
                    'average': round(avg_similarity, 4),
                    'maximum': round(max_similarity, 4),
                    'minimum': round(min_similarity, 4)
                },
                'metadata': {
                    'total_candidates': len(candidate_contents),
                    'valid_candidates': len(valid_candidate_contents),
                    'scored_contents': len(scored_contents),
                    'recommendation_count': len(recommendations),
                    'scoring_pending': len(contents_for_scoring)
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户 {user_id} 推荐失败: {e}")
            # 降级到随机推荐
            return self._get_random_recommendations(limit, content_type, fresh_days)
    
    def _get_random_recommendations(self, limit: int, content_type: str = None, 
                                   fresh_days: int = 30) -> Dict[str, Any]:
        """获取随机推荐（用于行为数不足或MBTI未建立时）"""
        try:
            # 获取候选内容
            candidate_contents = self.get_contents_for_recommendation(
                content_type=content_type,
                fresh_days=fresh_days,
                limit=1000
            )
            
            if not candidate_contents:
                logger.warning("数据库中没有候选内容")
                return {
                    'recommendations': [],
                    'user_mbti': None,
                    'similarity_stats': {'average': 0.0, 'maximum': 0.0, 'minimum': 0.0},
                    'metadata': {
                        'total_candidates': 0,
                        'valid_candidates': 0,
                        'scored_contents': 0,
                        'recommendation_count': 0,
                        'scoring_pending': 0
                    }
                }
            
            # 随机选择内容
            import random
            if len(candidate_contents) < limit:
                selected_contents = candidate_contents
            else:
                selected_contents = random.sample(candidate_contents, limit)
            
            # 构建推荐结果
            recommendations = []
            for content in selected_contents:
                recommendations.append({
                    'content_id': content.content_id,
                    'title': getattr(content, 'title', ''),
                    'similarity_score': 0.5,  # 随机推荐使用默认相似度
                    'mbti_vector': [0.5, 0.5, 0.5, 0.5]
                })
            
            return {
                'recommendations': recommendations,
                'user_mbti': None,
                'similarity_stats': {'average': 0.5, 'maximum': 0.5, 'minimum': 0.5},
                'metadata': {
                    'total_candidates': len(candidate_contents),
                    'valid_candidates': len(selected_contents),
                    'scored_contents': len(selected_contents),
                    'recommendation_count': len(recommendations),
                    'scoring_pending': 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取随机推荐失败: {e}")
            return {
                'recommendations': [],
                'user_mbti': None,
                'similarity_stats': {'average': 0.0, 'maximum': 0.0, 'minimum': 0.0},
                'metadata': {
                    'total_candidates': 0,
                    'valid_candidates': 0,
                    'scored_contents': 0,
                    'recommendation_count': 0,
                    'scoring_pending': 0
                }
            }
    
    def _get_similarity_based_recommendations(self, user_id: int, user_profile, 
                                            limit: int, content_type: str = None,
                                            similarity_threshold: float = 0.5,
                                            exclude_viewed: bool = True,
                                            fresh_days: int = 30) -> Dict[str, Any]:
        """基于MBTI相似度的推荐"""
        # 获取用户MBTI向量
        user_vector = [
            user_profile.E, user_profile.I, user_profile.S, user_profile.N,
            user_profile.T, user_profile.F, user_profile.J, user_profile.P
        ]
        
        # 获取排除的内容ID
        exclude_content_ids = []
        if exclude_viewed:
            exclude_content_ids = self.get_viewed_content_ids(user_id, fresh_days)
        
        # 获取候选内容 - 增加候选数量以确保有足够的内容筛选
        candidate_contents = self.get_contents_for_recommendation(
            content_type=content_type,
            fresh_days=fresh_days,
            exclude_content_ids=exclude_content_ids,
            limit=2000  # 增加到2000条，确保有足够的内容进行筛选
        )
        
        # 筛选有实际内容的内容
        valid_candidate_contents = [
            content for content in candidate_contents 
            if self._is_valid_content_for_recommendation(content.to_dict() if hasattr(content, 'to_dict') else content)
        ]
        
        if not valid_candidate_contents:
            return {
                "user_id": user_id,
                "user_mbti_type": user_profile.mbti_type,
                "user_mbti_probabilities": user_profile.to_dict()["probabilities"],
                "recommendations": [],
                "metadata": {
                    "total_candidates": len(candidate_contents),
                    "filtered_count": 0,
                    "valid_content_count": 0,
                    "avg_similarity": 0.0,
                    "generation_time": datetime.utcnow().isoformat(),
                    "algorithm_version": "v1.0",
                    "recommendation_type": "similarity",
                    "reason": "没有有效内容可推荐"
                }
            }
        
        # 计算相似度
        content_vectors = [content.get_vector() for content in valid_candidate_contents]
        similarities = self.calculate_mbti_similarity(user_vector, content_vectors)
        
        # 生成所有推荐
        all_recommendations = []
        for i, (content, similarity) in enumerate(zip(valid_candidate_contents, similarities)):
            all_recommendations.append({
                "content_id": content.content_id if hasattr(content, 'content_id') else content.get('id'),
                "similarity_score": round(similarity, 4),
                "rank": 0,
                "estimated_engagement": min(similarity * 0.8, 1.0),
                "recommendation_type": "similarity"
            })
        
        # 按相似度排序
        all_recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # 应用阈值过滤
        filtered_recommendations = [rec for rec in all_recommendations if rec["similarity_score"] >= similarity_threshold]
        
        # 如果过滤后不足limit条，返回前limit条最相似的
        if len(filtered_recommendations) < limit:
            recommendations = filtered_recommendations[:limit]
            logger.info(f"阈值过滤后推荐不足{limit}条，返回前{len(recommendations)}条最相似的")
        else:
            recommendations = filtered_recommendations[:limit]
        
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
                "valid_content_count": len(valid_candidate_contents),
                "filtered_count": len(recommendations),
                "avg_similarity": round(avg_similarity, 4),
                "generation_time": datetime.utcnow().isoformat(),
                "algorithm_version": "v1.0",
                "recommendation_type": "similarity",
                "cache_hit": False
            }
        }
        
        # 记录推荐日志
        self._log_recommendation(user_id, result, similarity_threshold, content_type, limit)
        
        return result
    

    

    
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
    
    def get_content_operation_users(self, content_id: int) -> List[int]:
        """获取对指定内容进行过操作的用户ID列表"""
        with self.get_session() as session:
            # 查询所有对该内容进行过操作的用户
            behaviors = session.query(UserBehavior).filter(
                UserBehavior.content_id == content_id
            ).all()
            
            # 提取唯一的用户ID
            user_ids = list(set([behavior.user_id for behavior in behaviors]))
            logger.info(f"内容 {content_id} 有 {len(user_ids)} 个操作用户")
            
            return user_ids
    
    def get_user_operation_posts(self, user_id: int) -> List[int]:
        """获取用户操作过的帖子ID列表"""
        with self.get_session() as session:
            # 查询用户的所有行为记录
            behaviors = session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id
            ).all()
            
            # 提取唯一的帖子ID
            post_ids = list(set([behavior.content_id for behavior in behaviors]))
            logger.info(f"用户 {user_id} 操作过 {len(post_ids)} 个帖子")
            
            return post_ids
    
    def update_content_mbti(self, content_id: int, probabilities: Dict[str, float]) -> ContentMBTI:
        """更新内容的MBTI评分"""
        with self.get_session() as session:
            # 查找现有记录
            content_mbti = session.query(ContentMBTI).filter(
                ContentMBTI.content_id == content_id
            ).first()
            
            if not content_mbti:
                logger.warning(f"内容 {content_id} 没有MBTI记录，无法更新")
                return None
            
            # 标准化概率
            normalized_probs = normalize_mbti_probabilities(probabilities)
            
            # 更新MBTI概率
            content_mbti.E = normalized_probs.get("E", 0.5)
            content_mbti.I = normalized_probs.get("I", 0.5)
            content_mbti.S = normalized_probs.get("S", 0.5)
            content_mbti.N = normalized_probs.get("N", 0.5)
            content_mbti.T = normalized_probs.get("T", 0.5)
            content_mbti.F = normalized_probs.get("F", 0.5)
            content_mbti.J = normalized_probs.get("J", 0.5)
            content_mbti.P = normalized_probs.get("P", 0.5)
            
            # 更新修改时间
            content_mbti.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(content_mbti)
            
            logger.info(f"内容 {content_id} MBTI评分更新完成")
            return content_mbti
    
    def get_total_recommendations_count(self, user_id: int, content_type: str = None,
                                      similarity_threshold: float = 0.5,
                                      exclude_viewed: bool = True,
                                      fresh_days: int = 30) -> int:
        """获取用户推荐的总数量（用于分页）"""
        try:
            # 获取用户MBTI特征
            user_profile = self.get_user_profile(user_id)
            if not user_profile:
                return 0
            
            # 获取候选内容
            candidate_contents = self.get_contents_for_recommendation(
                content_type=content_type,
                fresh_days=fresh_days,
                limit=1000  # 获取足够多的候选内容
            )
            
            if not candidate_contents:
                return 0
            
            # 计算相似度
            user_vector = user_profile.get_vector()
            content_vectors = [content.get_vector() for content in candidate_contents]
            similarities = self.calculate_mbti_similarity([user_vector], content_vectors)
            
            # 过滤相似度达标的内容
            valid_contents = []
            for i, similarity in enumerate(similarities):
                if similarity >= similarity_threshold:
                    valid_contents.append(candidate_contents[i])
            
            # 如果排除已浏览内容
            if exclude_viewed:
                viewed_content_ids = self.get_user_viewed_content_ids(user_id)
                valid_contents = [content for content in valid_contents 
                               if content.content_id not in viewed_content_ids]
            
            return len(valid_contents)
            
        except Exception as e:
            logger.error(f"获取用户 {user_id} 推荐总数失败: {e}")
            return 0
    
    def get_user_viewed_content_ids(self, user_id: int) -> List[int]:
        """获取用户已浏览的内容ID列表"""
        with self.get_session() as session:
            behaviors = session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id,
                UserBehavior.action == "view"
            ).all()
            
            return [behavior.content_id for behavior in behaviors]
    
    def update_content_info(self, content_id: int, sohu_content: Dict[str, Any]) -> bool:
        """更新帖子内容信息（从搜狐API获取的数据）"""
        try:
            with self.get_session() as session:
                content_mbti = session.query(ContentMBTI).filter(ContentMBTI.content_id == content_id).first()
                
                if not content_mbti:
                    logger.warning(f"内容 {content_id} 没有MBTI记录，无法更新内容信息")
                    return False
                
                # 更新帖子内容字段
                content_mbti.title = sohu_content.get("title")
                content_mbti.cover_image = sohu_content.get("coverImage") or sohu_content.get("coverUrl")
                content_mbti.content = sohu_content.get("content")
                content_mbti.author = sohu_content.get("userName") or sohu_content.get("nickName")
                
                # 处理发布时间
                publish_time_str = sohu_content.get("createTime") or sohu_content.get("publishTime")
                if publish_time_str:
                    try:
                        content_mbti.publish_time = datetime.fromisoformat(publish_time_str.replace('Z', '+00:00'))
                    except:
                        content_mbti.publish_time = None
                
                content_mbti.content_type = sohu_content.get("mediaContentType", "article").lower()
                
                session.commit()
                logger.info(f"内容 {content_id} 的帖子信息已更新")
                return True
                
        except Exception as e:
            logger.error(f"更新内容 {content_id} 的帖子信息失败: {e}")
            return False
    
    def get_user_recommendation_progress(self, user_id: int) -> Dict[str, Any]:
        """获取用户推荐进度"""
        with self.get_session() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                return {
                    "current_page": 0,
                    "last_recommendation_time": None,
                    "total_recommendations": 0
                }
            
            return {
                "current_page": profile.current_recommendation_page or 0,
                "last_recommendation_time": profile.last_recommendation_time.isoformat() if profile.last_recommendation_time else None,
                "total_recommendations": profile.total_behaviors_analyzed or 0
            }
    
    def update_user_recommendation_progress(self, user_id: int, current_page: int) -> bool:
        """更新用户推荐进度"""
        try:
            with self.get_session() as session:
                profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
                
                if not profile:
                    logger.warning(f"用户 {user_id} 没有档案，无法更新推荐进度")
                    return False
                
                profile.current_recommendation_page = current_page
                profile.last_recommendation_time = datetime.utcnow()
                
                session.commit()
                logger.info(f"用户 {user_id} 推荐进度已更新到第 {current_page} 页")
                return True
                
        except Exception as e:
            logger.error(f"更新用户 {user_id} 推荐进度失败: {e}")
            return False
    
    def get_next_recommendation_page(self, user_id: int) -> int:
        """获取用户下一推荐页数"""
        progress = self.get_user_recommendation_progress(user_id)
        return progress["current_page"] + 1

# 全局数据库服务实例
db_service = DatabaseService()
