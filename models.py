# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, Field
import json

Base = declarative_base()

# =============================================================================
# SQLAlchemy ORM模型
# =============================================================================

class UserProfile(Base):
    """用户MBTI档案表"""
    __tablename__ = "user_mbti_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # MBTI概率分布
    E = Column(Float, default=0.5)  # 外向
    I = Column(Float, default=0.5)  # 内向
    S = Column(Float, default=0.5)  # 感觉
    N = Column(Float, default=0.5)  # 直觉
    T = Column(Float, default=0.5)  # 思维
    F = Column(Float, default=0.5)  # 情感
    J = Column(Float, default=0.5)  # 判断
    P = Column(Float, default=0.5)  # 知觉
    
    # 推导的MBTI类型
    mbti_type = Column(String(4), default="")
    
    # 置信度评分
    confidence_E_I = Column(Float, default=0.0)
    confidence_S_N = Column(Float, default=0.0)
    confidence_T_F = Column(Float, default=0.0)
    confidence_J_P = Column(Float, default=0.0)
    
    # 统计信息
    total_behaviors_analyzed = Column(Integer, default=0)
    behaviors_since_last_update = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 推荐进度跟踪
    current_recommendation_page = Column(Integer, default=0)  # 当前推荐到的页数
    last_recommendation_time = Column(DateTime, default=datetime.utcnow)  # 最后推荐时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "probabilities": {
                "E": self.E, "I": self.I,
                "S": self.S, "N": self.N,
                "T": self.T, "F": self.F,
                "J": self.J, "P": self.P
            },
            "mbti_type": self.mbti_type,
            "confidence_scores": {
                "E_I": self.confidence_E_I,
                "S_N": self.confidence_S_N,
                "T_F": self.confidence_T_F,
                "J_P": self.confidence_J_P
            },
            "total_behaviors_analyzed": self.total_behaviors_analyzed,
            "behaviors_since_last_update": self.behaviors_since_last_update,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "recommendation_progress": {
                "current_page": self.current_recommendation_page,
                "last_recommendation_time": self.last_recommendation_time.isoformat() if self.last_recommendation_time else None
            }
        }

class UserBehavior(Base):
    """用户行为记录表"""
    __tablename__ = "user_post_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    content_id = Column(Integer, nullable=False, index=True)
    
    # 行为信息
    action = Column(String(20), nullable=False)  # like, collect, comment, share, view
    weight = Column(Float, default=0.1)
    source = Column(String(50), default="unknown")  # recommendation, search, trending
    session_id = Column(String(100), nullable=True)
    
    # 时间信息
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 额外数据（JSON格式）
    extra_data = Column(JSON, nullable=True)
    
    # 索引
    __table_args__ = (
        {"mysql_charset": "utf8mb4"},
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "behavior_id": self.id,
            "user_id": self.user_id,
            "content_id": self.content_id,
            "action": self.action,
            "weight": self.weight,
            "source": self.source,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "extra_data": self.extra_data
        }

class ContentMBTI(Base):
    """内容MBTI评价表"""
    __tablename__ = "mbti_post_evaluations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, nullable=False, index=True)
    
    # 帖子内容字段（从搜狐API获取）
    title = Column(String(500), nullable=True)  # 帖子标题
    cover_image = Column(String(1000), nullable=True)  # 封面图URL
    content = Column(Text, nullable=True)  # 帖子内容
    author = Column(String(100), nullable=True)  # 作者
    publish_time = Column(DateTime, nullable=True)  # 发布时间
    content_type = Column(String(50), default="article")  # 内容类型
    
    # MBTI概率分布
    E = Column(Float, default=0.5)
    I = Column(Float, default=0.5) 
    S = Column(Float, default=0.5)
    N = Column(Float, default=0.5)
    T = Column(Float, default=0.5)
    F = Column(Float, default=0.5)
    J = Column(Float, default=0.5)
    P = Column(Float, default=0.5)
    
    # 元数据
    model_version = Column(String(20), default="v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_vector(self) -> List[float]:
        """获取MBTI向量"""
        return [self.E, self.I, self.S, self.N, self.T, self.F, self.J, self.P]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content_id": self.content_id,
            "title": self.title,
            "cover_image": self.cover_image,
            "content": self.content,
            "author": self.author,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "content_type": self.content_type,
            "mbti_vector": self.get_vector(),
            "probabilities": {
                "E": self.E, "I": self.I,
                "S": self.S, "N": self.N,
                "T": self.T, "F": self.F,
                "J": self.J, "P": self.P
            },
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class RecommendationLog(Base):
    """推荐日志表"""
    __tablename__ = "recommendation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # 推荐结果
    recommended_content_ids = Column(JSON, nullable=False)  # 推荐的内容ID列表
    similarity_scores = Column(JSON, nullable=False)        # 对应的相似度分数
    
    # 推荐参数
    limit = Column(Integer, default=50)
    content_type_filter = Column(String(50), nullable=True)
    similarity_threshold = Column(Float, default=0.5)
    
    # 算法信息
    algorithm_version = Column(String(20), default="v1.0")
    total_candidates = Column(Integer, default=0)
    avg_similarity = Column(Float, default=0.0)
    
    # 用户MBTI快照
    user_mbti_snapshot = Column(JSON, nullable=True)
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Integer, default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "log_id": self.id,
            "user_id": self.user_id,
            "recommended_content_ids": self.recommended_content_ids,
            "similarity_scores": self.similarity_scores,
            "limit": self.limit,
            "algorithm_version": self.algorithm_version,
            "total_candidates": self.total_candidates,
            "avg_similarity": self.avg_similarity,
            "user_mbti_snapshot": self.user_mbti_snapshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "response_time_ms": self.response_time_ms
        }

# =============================================================================
# Pydantic模型（API请求/响应）
# =============================================================================

class BehaviorRecordRequest(BaseModel):
    """记录用户行为请求模型"""
    user_id: int = Field(..., description="用户ID")
    content_id: int = Field(..., description="内容ID") 
    action: str = Field(..., description="行为类型", pattern="^(view|like|collect|comment|share|follow)$")
    timestamp: Optional[datetime] = Field(None, description="行为时间")
    source: Optional[str] = Field("unknown", description="行为来源")
    session_id: Optional[str] = Field(None, description="会话ID")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")

class BehaviorRecordResponse(BaseModel):
    """记录用户行为响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class UserHistoryRequest(BaseModel):
    """用户历史查询请求模型"""
    action: Optional[str] = Field(None, description="行为类型过滤")
    limit: int = Field(50, ge=1, le=100, description="返回数量")
    offset: int = Field(0, ge=0, description="偏移量")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")

class UserHistoryResponse(BaseModel):
    """用户历史查询响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    limit: int = Field(50, ge=1, le=100, description="推荐数量")
    content_type: Optional[str] = Field(None, description="内容类型过滤")
    similarity_threshold: float = Field(0.5, ge=0.1, le=0.9, description="相似度阈值")
    exclude_viewed: bool = Field(True, description="是否排除已浏览")
    fresh_days: int = Field(30, ge=1, le=365, description="内容新鲜度天数")

class RecommendationResponse(BaseModel):
    """推荐响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class MBTIProfileResponse(BaseModel):
    """MBTI档案响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class MBTIUpdateRequest(BaseModel):
    """MBTI更新请求模型"""
    force_update: bool = Field(False, description="强制更新")
    analyze_last_n_behaviors: int = Field(100, ge=10, le=500, description="分析最近N个行为")

class MBTIUpdateResponse(BaseModel):
    """MBTI更新响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class ContentDetailResponse(BaseModel):
    """内容详情响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class BatchContentRequest(BaseModel):
    """批量内容请求模型"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    include_mbti: bool = Field(True, description="是否包含MBTI分析")

class BatchContentResponse(BaseModel):
    """批量内容响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

class APIErrorResponse(BaseModel):
    """API错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# =============================================================================
# 数据库工具函数
# =============================================================================

def create_database_engine(database_url: str):
    """创建数据库引擎"""
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

def create_tables(engine):
    """创建所有表"""
    Base.metadata.create_all(engine)

def get_session_factory(engine):
    """获取Session工厂"""
    return sessionmaker(bind=engine)

# =============================================================================
# MBTI工具函数
# =============================================================================

def get_mbti_type_from_probabilities(probabilities: Dict[str, float]) -> str:
    """根据概率分布推导MBTI类型"""
    mbti_type = ""
    mbti_type += "E" if probabilities.get("E", 0.5) > probabilities.get("I", 0.5) else "I"
    mbti_type += "S" if probabilities.get("S", 0.5) > probabilities.get("N", 0.5) else "N"
    mbti_type += "T" if probabilities.get("T", 0.5) > probabilities.get("F", 0.5) else "F"
    mbti_type += "J" if probabilities.get("J", 0.5) > probabilities.get("P", 0.5) else "P"
    return mbti_type

def calculate_confidence_scores(probabilities: Dict[str, float]) -> Dict[str, float]:
    """计算置信度分数"""
    return {
        "E_I": abs(probabilities.get("E", 0.5) - probabilities.get("I", 0.5)),
        "S_N": abs(probabilities.get("S", 0.5) - probabilities.get("N", 0.5)),
        "T_F": abs(probabilities.get("T", 0.5) - probabilities.get("F", 0.5)),
        "J_P": abs(probabilities.get("J", 0.5) - probabilities.get("P", 0.5))
    }

def normalize_mbti_probabilities(probabilities: Dict[str, float]) -> Dict[str, float]:
    """标准化MBTI概率，确保每对和为1.0"""
    normalized = probabilities.copy()
    
    pairs = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
    for pair in pairs:
        total = normalized.get(pair[0], 0.5) + normalized.get(pair[1], 0.5)
        if total > 0:
            normalized[pair[0]] = normalized.get(pair[0], 0.5) / total
            normalized[pair[1]] = normalized.get(pair[1], 0.5) / total
        else:
            normalized[pair[0]] = 0.5
            normalized[pair[1]] = 0.5
    
    return normalized
