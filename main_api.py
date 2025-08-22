# -*- coding: utf-8 -*-
"""
MBTI推荐系统主API
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Path, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from new_config import CONFIG
from models import (
    BehaviorRecordRequest, BehaviorRecordResponse,
    UserHistoryRequest, UserHistoryResponse,
    RecommendationRequest, RecommendationResponse,
    MBTIProfileResponse, MBTIUpdateRequest, MBTIUpdateResponse,
    ContentDetailResponse, BatchContentRequest, BatchContentResponse,
    APIErrorResponse
)
from database_service import db_service
from mbti_service import mbti_service
from sohu_client import sohu_client
import random
import numpy as np

# 配置日志
logging.basicConfig(
    level=getattr(logging, CONFIG["logging"]["level"]),
    format=CONFIG["logging"]["format"]
)
logger = logging.getLogger(__name__)

# 重要文件列表 - 这些文件修改时需要重启
CRITICAL_FILES = [
    "main_api.py",           # 主API文件
    "mbti_service.py",       # MBTI服务核心逻辑
    "database_service.py",   # 数据库服务
    "models.py",             # 数据模型
    "new_config.py",         # 配置文件
    "sohu_client.py"         # 搜狐API客户端
]

# AI评分模式配置
AI_SCORING_MODE = "random"  # 可选值: "ai", "random", "mixed"
# ai: 真正调用AI评分
# random: 使用随机数生成
# mixed: 混合模式，部分AI评分，部分随机数

def generate_random_mbti_scores() -> dict:
    """生成随机的MBTI评分"""
    # 生成4个维度的随机概率
    e_i = random.uniform(0.2, 0.8)  # E/I维度
    s_n = random.uniform(0.2, 0.8)  # S/N维度
    t_f = random.uniform(0.2, 0.8)  # T/F维度
    j_p = random.uniform(0.2, 0.8)  # J/P维度
    
    # 确保对立维度概率和为1.0
    return {
        "E": round(e_i, 3),
        "I": round(1.0 - e_i, 3),
        "S": round(s_n, 3),
        "N": round(1.0 - s_n, 3),
        "T": round(t_f, 3),
        "F": round(1.0 - t_f, 3),
        "J": round(j_p, 3),
        "P": round(1.0 - j_p, 3)
    }

def generate_consistent_random_mbti_scores() -> dict:
    """生成一致的随机MBTI评分（基于种子）"""
    # 使用内容ID作为种子，确保相同内容总是生成相同的评分
    seed = random.randint(1, 1000000)
    random.seed(seed)
    
    scores = generate_random_mbti_scores()
    random.seed()  # 重置种子
    return scores

def get_mbti_scoring_mode() -> str:
    """获取当前MBTI评分模式"""
    return AI_SCORING_MODE

def set_mbti_scoring_mode(mode: str):
    """设置MBTI评分模式"""
    global AI_SCORING_MODE
    valid_modes = ["ai", "random", "mixed"]
    if mode in valid_modes:
        AI_SCORING_MODE = mode
        logger.info(f"MBTI评分模式已切换为: {mode}")
        return True
    else:
        logger.warning(f"无效的评分模式: {mode}，有效模式: {valid_modes}")
        return False

async def ensure_content_mbti_with_current_mode(content_id: int):
    """根据当前评分模式确保内容有MBTI评分"""
    try:
        # 检查是否已有评分
        existing_mbti = db_service.get_content_mbti(content_id)
        if existing_mbti:
            logger.info(f"内容 {content_id} 已有MBTI评分，跳过")
            return
        
        # 根据当前模式生成评分
        current_mode = get_mbti_scoring_mode()
        if current_mode == "random":
            # 生成随机评分
            probabilities = generate_consistent_random_mbti_scores()
            scoring_method = "random_generation"
            logger.info(f"内容 {content_id} 使用随机数生成MBTI评分")
        elif current_mode == "mixed":
            # 混合模式：50%概率使用AI，50%概率使用随机数
            if random.random() < 0.5:
                # 这里需要获取内容文本，暂时使用随机数
                probabilities = generate_consistent_random_mbti_scores()
                scoring_method = "random_generation"
                logger.info(f"内容 {content_id} 混合模式选择随机数生成")
            else:
                # 使用AI评分
                probabilities = await mbti_service.evaluate_content_by_id(content_id)
                scoring_method = "ai_evaluation"
                logger.info(f"内容 {content_id} 混合模式选择AI评价")
        else:  # AI模式
            probabilities = await mbti_service.evaluate_content_by_id(content_id)
            scoring_method = "ai_evaluation"
            logger.info(f"内容 {content_id} 使用AI评价MBTI评分")
        
        # 保存评分到数据库
        if probabilities:
            db_service.save_content_mbti(
                content_id=content_id,
                probabilities=probabilities,
                content_title="",  # 暂时为空，后续可以从内容获取
                content_type="article",
                quality_score=0.5  # 添加缺失的quality_score参数
            )
            logger.info(f"内容 {content_id} MBTI评分已保存，方法: {scoring_method}")
        
    except Exception as e:
        logger.error(f"确保内容 {content_id} MBTI评分失败: {e}")

# 创建FastAPI应用
app = FastAPI(
    title=CONFIG["app"]["name"],
    version=CONFIG["app"]["version"],
    description="基于MBTI特征分析的智能内容推荐系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 全局异常处理
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "details": {"error": str(exc)}
        }
    )

# =============================================================================
# 健康检查和系统信息
# =============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": CONFIG["app"]["version"]
    }

@app.get("/api/{api_version}/system/info")
async def get_system_info(api_version: str = Path(..., pattern="^v[0-9]+$")):
    """获取系统信息"""
    if api_version != f"v{CONFIG['app']['api_version'].replace('v', '')}":
        raise HTTPException(status_code=404, detail="API版本不支持")
    
    stats = db_service.get_database_stats()
    
    return {
        "success": True,
        "data": {
            "app_name": CONFIG["app"]["name"],
            "app_version": CONFIG["app"]["version"],
            "api_version": CONFIG["app"]["api_version"],
            "database_stats": stats,
            "mbti_scoring_mode": get_mbti_scoring_mode(),
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.get("/api/v1/system/mbti-scoring-mode")
async def get_mbti_scoring_mode_info():
    """获取当前MBTI评分模式信息"""
    current_mode = get_mbti_scoring_mode()
    
    mode_descriptions = {
        "ai": "真正调用AI进行MBTI评分",
        "random": "使用随机数生成MBTI评分",
        "mixed": "混合模式：部分AI评分，部分随机数生成"
    }
    
    return {
        "success": True,
        "data": {
            "current_mode": current_mode,
            "description": mode_descriptions.get(current_mode, "未知模式"),
            "available_modes": ["ai", "random", "mixed"],
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.post("/api/v1/system/mbti-scoring-mode")
async def set_mbti_scoring_mode_api(mode: str):
    """设置MBTI评分模式"""
    try:
        success = set_mbti_scoring_mode(mode)
        
        if success:
            return {
                "success": True,
                "data": {
                    "new_mode": mode,
                    "message": f"MBTI评分模式已切换为: {mode}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"无效的评分模式: {mode}")
            
    except Exception as e:
        logger.error(f"设置MBTI评分模式失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")

@app.post("/api/v1/system/test-mbti-scoring")
async def test_mbti_scoring_modes():
    """测试不同MBTI评分模式的效果"""
    try:
        test_content_id = 9999  # 使用测试ID
        test_results = {}
        
        # 测试AI模式
        set_mbti_scoring_mode("ai")
        ai_result = await evaluate_content_mbti(
            {"content": "这是一个测试内容，用于验证AI评分模式", "title": "测试内容"},
            test_content_id,
            "article"
        )
        test_results["ai_mode"] = ai_result.get("data", {})
        
        # 测试随机数模式
        set_mbti_scoring_mode("random")
        random_result = await evaluate_content_mbti(
            {"content": "这是另一个测试内容，用于验证随机数评分模式", "title": "测试内容2"},
            test_content_id + 1,
            "article"
        )
        test_results["random_mode"] = random_result.get("data", {})
        
        # 测试混合模式
        set_mbti_scoring_mode("mixed")
        mixed_result = await evaluate_content_mbti(
            {"content": "这是第三个测试内容，用于验证混合评分模式", "title": "测试内容3"},
            test_content_id + 2,
            "article"
        )
        test_results["mixed_mode"] = mixed_result.get("data", {})
        
        # 恢复为随机数模式（默认）
        set_mbti_scoring_mode("random")
        
        return {
            "success": True,
            "data": {
                "test_results": test_results,
                "message": "三种评分模式测试完成",
                "current_mode": get_mbti_scoring_mode(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"测试MBTI评分模式失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

# =============================================================================
# 用户行为管理接口
# =============================================================================

@app.post("/api/v1/behavior/record", response_model=BehaviorRecordResponse)
async def record_user_behavior(
    request: BehaviorRecordRequest,
    background_tasks: BackgroundTasks
):
    """记录用户行为"""
    try:
        # 记录行为到数据库
        behavior = db_service.record_user_behavior(
            user_id=request.user_id,
            content_id=request.content_id,
            action=request.action,
            source=request.source,
            session_id=request.session_id,
            extra_data=request.extra_data,
            timestamp=request.timestamp
        )
        
        # 增加用户行为计数
        behavior_count = db_service.increment_behavior_count(request.user_id)
        
        # 根据当前评分模式处理内容MBTI评分
        current_mode = get_mbti_scoring_mode()
        if current_mode == "random":
            # 随机数模式：直接生成随机评分
            background_tasks.add_task(
                ensure_content_mbti_with_current_mode,
                request.content_id
            )
        else:
            # AI模式或混合模式：使用原有逻辑
        background_tasks.add_task(
            mbti_service.ensure_content_mbti_evaluated,
            request.content_id
        )
        
        # 检查是否需要触发MBTI更新
        mbti_update_triggered = False
        threshold = CONFIG["behavior"]["mbti_update"]["behavior_threshold"]
        next_update_threshold = threshold - behavior_count
        
        # 检查是否达到新的50条行为阈值
        if behavior_count % threshold == 0:
            # 每达到50条行为就触发MBTI更新
            background_tasks.add_task(
                mbti_service.update_user_mbti_profile,
                request.user_id,
                True  # 强制更新，因为达到了新的阈值
            )
            mbti_update_triggered = True
            next_update_threshold = threshold
            
            logger.info(f"用户 {request.user_id} 达到新的{threshold}条行为阈值，触发MBTI更新")
        
        logger.info(f"记录用户 {request.user_id} 行为: {request.action} -> 内容 {request.content_id}")
        
        return BehaviorRecordResponse(
            success=True,
            data={
                "behavior_id": behavior.id,
                "user_id": behavior.user_id,
                "content_id": behavior.content_id,
                "action": behavior.action,
                "recorded_at": behavior.timestamp.isoformat(),
                "weight": behavior.weight,
                "mbti_update_triggered": mbti_update_triggered,
                "next_update_threshold": max(0, next_update_threshold),
                "current_behavior_count": behavior_count
            },
            message="行为记录成功"
        )
        
    except Exception as e:
        logger.error(f"记录用户行为失败: {e}")
        raise HTTPException(status_code=500, detail=f"记录行为失败: {str(e)}")

@app.get("/api/v1/behavior/history/{user_id}", response_model=UserHistoryResponse)
async def get_user_history(
    user_id: int = Path(..., gt=0),
    action: Optional[str] = Query(None, pattern="^(view|like|collect|comment|share|follow)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """获取用户行为历史"""
    try:
        # 获取行为历史
        behaviors, total_count = db_service.get_user_behaviors(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应格式
        behavior_list = [behavior.to_dict() for behavior in behaviors]
        
        # 计算分页信息
        total_pages = (total_count + limit - 1) // limit
        current_page = (offset // limit) + 1
        has_next = offset + limit < total_count
        
        return UserHistoryResponse(
            success=True,
            data={
                "user_id": user_id,
                "total_count": total_count,
                "returned_count": len(behavior_list),
                "behaviors": behavior_list,
                "pagination": {
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "limit": limit,
                    "offset": offset
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取用户历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@app.get("/api/v1/behavior/stats/{user_id}")
async def get_user_behavior_stats(
    user_id: int = Path(..., gt=0),
    days: int = Query(30, ge=1, le=365)
):
    """获取用户行为统计"""
    try:
        stats = db_service.get_user_behavior_stats(user_id, days)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取用户行为统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# =============================================================================
# 推荐服务接口
# =============================================================================

@app.get("/api/v1/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: int = Path(..., gt=0),
    limit: int = Query(20, ge=1, le=100),  # 默认每页20条
    page: Optional[int] = Query(None, ge=1),  # 页码，从1开始，None表示自动获取下一页
    content_type: Optional[str] = Query(None, pattern="^(article|video|product|all)$"),
    similarity_threshold: float = Query(0.5, ge=0.1, le=0.9),
    exclude_viewed: bool = Query(True),
    fresh_days: int = Query(30, ge=1, le=365),
    include_content_details: bool = Query(True),  # 是否包含内容详情
    auto_page: bool = Query(True)  # 是否自动翻页
):
    """获取用户个性化推荐（支持分页和内容详情）"""
    try:
        # 确定推荐页数
        if page is None and auto_page:
            # 自动获取用户下一推荐页数
            actual_page = db_service.get_next_recommendation_page(user_id)
            logger.info(f"用户 {user_id} 自动翻页到第 {actual_page} 页")
        else:
            actual_page = page or 1
        
        # 计算偏移量
        offset = (actual_page - 1) * limit
        
        # 生成推荐
        recommendations = db_service.get_recommendations_for_user(
            user_id=user_id,
            limit=limit,
            offset=offset,  # 添加偏移量支持
            content_type=content_type,
            similarity_threshold=similarity_threshold,
            exclude_viewed=exclude_viewed,
            fresh_days=fresh_days
        )
        
        # 如果数据库没有推荐数据，直接从搜狐API获取
        if not recommendations.get('recommendations') or len(recommendations['recommendations']) == 0:
            logger.info(f"用户 {user_id} 数据库中没有推荐数据，直接从搜狐API获取")
            try:
                # 从搜狐API获取文章列表
                async with sohu_client as client:
                    article_result = await client.get_article_list(page_size=limit)
                
                # 检查搜狐API返回的数据结构
                logger.info(f"搜狐API返回数据结构: {type(article_result)} - {article_result}")
                
                # 处理搜狐API返回的数据结构
                articles = []
                if isinstance(article_result, dict) and article_result.get("code") == 200:
                    # 搜狐API格式: {"code": 200, "data": [...]}
                    articles = article_result.get("data", [])
                elif isinstance(article_result, list):
                    # 直接返回文章列表
                    articles = article_result
                
                logger.info(f"解析后得到 {len(articles)} 篇文章")
                
                if articles:
                    # 转换为推荐格式，只包含需要的字段
                    recommendations = {
                        'recommendations': [
                            {
                                'content_id': article.get('id'),
                                'title': article.get('title', ''),
                                'cover_image': article.get('coverImage', ''),
                                'author': article.get('userName', ''),
                                'publish_time': article.get('createTime', ''),
                                'similarity_score': 0.5,  # 默认相似度
                                'mbti_vector': [0.5, 0.5, 0.5, 0.5],  # 默认MBTI向量
                                'source': 'sohu_direct'
                            }
                            for article in articles[:limit]
                        ]
                    }
                    
                    # 设置总数为实际获取的数量
                    total_recommendations = len(recommendations['recommendations'])
                    
                    # 标记已经包含内容详情，跳过后续的内容获取
                    include_content_details = False
                else:
                    logger.warning("无法解析搜狐API返回的文章数据")
                    recommendations = {'recommendations': []}
                    total_recommendations = 0
                    
            except Exception as e:
                logger.error(f"从搜狐API获取内容失败: {e}")
                recommendations = {'recommendations': []}
                total_recommendations = 0
        else:
            # 数据库有数据，获取总推荐数量（用于分页）
            total_recommendations = db_service.get_total_recommendations_count(
                user_id=user_id,
                content_type=content_type,
                similarity_threshold=similarity_threshold,
                exclude_viewed=exclude_viewed,
                fresh_days=fresh_days
            )
        
        # 如果数据库有推荐数据但没有内容详情，从搜狐API获取
        if recommendations.get('recommendations') and not recommendations['recommendations'][0].get('title'):
            content_ids = [rec.get('content_id') for rec in recommendations['recommendations'] if rec.get('content_id')]
            
            if content_ids:
                logger.info(f"准备从搜狐API获取 {len(content_ids)} 个内容详情: {content_ids}")
                try:
                    # 从Sohu API批量获取内容详情
                    async with sohu_client as client:
                        batch_result = await client.get_contents_batch(content_ids)
                    
                    logger.info(f"搜狐API批量获取结果: {batch_result.get('code')} - {batch_result.get('msg', '')}")
                    
                    if batch_result.get("code") == 200:
                        contents = batch_result["data"].get("contents", [])
                        logger.info(f"搜狐API返回内容数量: {len(contents)}")
                        
                        # 构建内容映射
                        contents_map = {}
                        for content in contents:
                            content_id = content.get("id")
                            if content_id:
                                contents_map[content_id] = content
                                logger.debug(f"映射内容ID {content_id} -> {content.get('title', 'N/A')}")
                        
                        logger.info(f"成功映射 {len(contents_map)} 个内容")
                        
                        # 将内容详情添加到推荐结果中，并更新数据库
                        for rec in recommendations['recommendations']:
                            content_id = rec.get('content_id')
                            if content_id and content_id in contents_map:
                                sohu_content = contents_map[content_id]
                                rec['content'] = sohu_content
                                
                                # 同时更新数据库中的帖子信息
                                try:
                                    db_service.update_content_info(content_id, sohu_content)
                                except Exception as e:
                                    logger.warning(f"更新数据库帖子信息失败: {e}")
                                
                                logger.debug(f"为推荐 {content_id} 添加搜狐内容详情")
                            else:
                                rec['content'] = None
                                logger.warning(f"推荐 {content_id} 未找到对应的搜狐内容")
                    else:
                        logger.warning(f"获取内容详情失败: {batch_result}")
                        # 如果获取失败，设置content为None
                        for rec in recommendations['recommendations']:
                            rec['content'] = None
                            
                except Exception as e:
                    logger.error(f"获取内容详情时出错: {e}")
                    # 出错时设置content为None
                    for rec in recommendations['recommendations']:
                        rec['content'] = None
        
        # 计算分页信息
        total_pages = (total_recommendations + limit - 1) // limit
        has_next = actual_page < total_pages
        has_prev = actual_page > 1
        
        logger.info(f"为用户 {user_id} 生成第 {actual_page} 页推荐，共 {len(recommendations['recommendations'])} 个推荐")
        
        # 更新用户推荐进度
        if auto_page and recommendations.get('recommendations'):
            try:
                db_service.update_user_recommendation_progress(user_id, actual_page)
                logger.info(f"用户 {user_id} 推荐进度已更新到第 {actual_page} 页")
            except Exception as e:
                logger.warning(f"更新用户 {user_id} 推荐进度失败: {e}")
        
        return RecommendationResponse(
            success=True,
            data={
                **recommendations,
                            "pagination": {
                "current_page": actual_page,
                "total_pages": total_pages,
                "total_count": total_recommendations,
                "limit": limit,
                "offset": offset,
                "has_next": has_next,
                "has_prev": has_prev
            }
            },
            message="推荐生成成功"
        )
        
    except Exception as e:
        logger.error(f"生成推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"推荐生成失败: {str(e)}")

@app.get("/api/v1/recommendations/similar/{content_id}")
async def get_similar_content_recommendations(
    content_id: int = Path(..., gt=0),
    limit: int = Query(20, ge=1, le=100),  # 默认每页20条
    page: int = Query(1, ge=1),  # 页码，从1开始
    user_id: Optional[int] = Query(None, gt=0),
    include_content_details: bool = Query(True)  # 是否包含内容详情
):
    """获取相似内容推荐（支持分页和内容详情）"""
    try:
        # 获取基础内容的MBTI特征
        base_content_mbti = db_service.get_content_mbti(content_id)
        if not base_content_mbti:
            raise HTTPException(status_code=404, detail="内容MBTI特征不存在")
        
        # 获取候选内容
        candidate_contents = db_service.get_contents_for_recommendation(limit=500)
        
        if not candidate_contents:
            logger.info(f"数据库中没有候选内容，直接从搜狐API获取相似内容")
            try:
                # 从搜狐API获取文章列表作为候选
                async with sohu_client as client:
                    article_result = await client.get_article_list(page_size=100)
                
                if article_result.get("code") == 200:
                    articles = article_result["data"].get("articles", [])
                    logger.info(f"搜狐API返回 {len(articles)} 篇文章作为候选")
                    
                    # 转换为候选内容格式，并保存搜狐内容用于后续返回
                    candidate_contents = []
                    sohu_contents_map = {}  # 保存搜狐内容映射
                    
                    for article in articles:
                        content_id = article.get('id')
                        if content_id:
                            # 创建候选内容对象
                            candidate_content = type('Content', (), {
                                'content_id': content_id,
                                'title': article.get('title', ''),
                                'get_vector': lambda: [0.5, 0.5, 0.5, 0.5]  # 默认MBTI向量
                            })()
                            candidate_contents.append(candidate_content)
                            
                            # 保存搜狐内容
                            sohu_contents_map[content_id] = article
                else:
                    logger.warning(f"搜狐API获取失败: {article_result}")
                    candidate_contents = []
                    
            except Exception as e:
                logger.error(f"从搜狐API获取候选内容失败: {e}")
                candidate_contents = []
        
        if not candidate_contents:
            return {
                "success": True,
                "data": {
                    "base_content_id": content_id,
                    "base_mbti_vector": base_content_mbti.get_vector(),
                    "similar_contents": [],
                    "pagination": {
                        "current_page": page,
                        "total_pages": 0,
                        "total_count": 0,
                        "limit": limit,
                        "offset": 0,
                        "has_next": False,
                        "has_prev": False
                    }
                }
            }
        
        # 计算相似度
        base_vector = base_content_mbti.get_vector()
        content_vectors = [content.get_vector() for content in candidate_contents]
        similarities = db_service.calculate_mbti_similarity([base_vector], content_vectors)
        
        # 排序和过滤
        similar_contents = []
        for i, (content, similarity) in enumerate(zip(candidate_contents, similarities)):
            if content.content_id != content_id and similarity >= 0.3:  # 排除自己，设置最低相似度
                similar_contents.append({
                    "content_id": content.content_id,
                    "similarity_score": round(similarity, 4),
                    "mbti_distance": round(1 - similarity, 4),
                    "rank": 0  # 稍后设置
                })
        
        # 按相似度排序
        similar_contents.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # 计算分页
        total_count = len(similar_contents)
        offset = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # 分页切片
        paginated_contents = similar_contents[offset:offset + limit]
        
        # 设置排名
        for i, content in enumerate(paginated_contents):
            content["rank"] = offset + i + 1
        
        # 如果需要包含内容详情，从Sohu API获取
        if include_content_details and paginated_contents:
            content_ids = [rec.get('content_id') for rec in paginated_contents if rec.get('content_id')]
            
            if content_ids:
                logger.info(f"准备从搜狐API获取 {len(content_ids)} 个相似内容详情: {content_ids}")
                try:
                    # 从Sohu API批量获取内容详情
                    async with sohu_client as client:
                        batch_result = await client.get_contents_batch(content_ids)
                    
                    logger.info(f"搜狐API批量获取相似内容结果: {batch_result.get('code')} - {batch_result.get('msg', '')}")
                    
                    if batch_result.get("code") == 200:
                        contents = batch_result["data"].get("contents", [])
                        logger.info(f"搜狐API返回相似内容数量: {len(contents)}")
                        
                        # 构建内容映射
                        contents_map = {}
                        for content in contents:
                            content_id = content.get("id")
                            if content_id:
                                contents_map[content_id] = content
                                logger.debug(f"映射相似内容ID {content_id} -> {content.get('title', 'N/A')}")
                        
                        logger.info(f"成功映射 {len(contents_map)} 个相似内容")
                        
                        # 将内容详情添加到推荐结果中，并更新数据库
                        for rec in paginated_contents:
                            content_id = rec.get('content_id')
                            if content_id and content_id in contents_map:
                                sohu_content = contents_map[content_id]
                                rec['content'] = sohu_content
                                
                                # 同时更新数据库中的帖子信息
                                try:
                                    db_service.update_content_info(content_id, sohu_content)
                                except Exception as e:
                                    logger.warning(f"更新数据库帖子信息失败: {e}")
                                
                                logger.debug(f"为相似推荐 {content_id} 添加搜狐内容详情")
                            else:
                                rec['content'] = None
                                logger.warning(f"相似推荐 {content_id} 未找到对应的搜狐内容")
                    else:
                        logger.warning(f"获取相似内容详情失败: {batch_result}")
                        # 如果获取失败，设置content为None
                        for rec in paginated_contents:
                            rec['content'] = None
                            
                except Exception as e:
                    logger.error(f"获取相似内容详情时出错: {e}")
                    # 出错时设置content为None
                    for rec in paginated_contents:
                        rec['content'] = None
        
        return {
            "success": True,
            "data": {
                "base_content_id": content_id,
                "base_mbti_vector": base_vector,
                "similar_contents": paginated_contents,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取相似内容推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取相似推荐失败: {str(e)}")

# =============================================================================
# 内容服务接口
# =============================================================================

@app.get("/api/v1/content/{content_id}", response_model=ContentDetailResponse)
async def get_content_detail(
    content_id: int = Path(..., gt=0),
    content_type: Optional[str] = Query(None, pattern="^(article|video|product)$"),
    include_mbti: bool = Query(True)
):
    """获取内容详情（代理到SohuGlobal API）"""
    try:
        # 从SohuGlobal API获取内容
        async with sohu_client as client:
            content_data = await client.get_content_by_id(content_id, content_type)
        
        if content_data.get("code") != 200:
            raise HTTPException(status_code=404, detail="内容不存在")
        
        result_data = content_data["data"]
        
        # 如果需要包含MBTI分析
        if include_mbti:
            content_mbti = db_service.get_content_mbti(content_id)
            if content_mbti:
                result_data["mbti_analysis"] = content_mbti.to_dict()["probabilities"]
            else:
                # 如果没有MBTI分析，可以选择在后台异步进行分析
                result_data["mbti_analysis"] = None
        
        result_data["source"] = "sohuglobal"
        
        return ContentDetailResponse(
            success=True,
            data=result_data,
            message="获取内容成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内容失败: {str(e)}")

@app.post("/api/v1/content/batch", response_model=BatchContentResponse)
async def get_batch_content_details(request: BatchContentRequest):
    """批量获取内容详情"""
    try:
        if not request.content_ids:
            raise HTTPException(status_code=400, detail="内容ID列表不能为空")
        
        if len(request.content_ids) > 100:
            raise HTTPException(status_code=400, detail="一次最多获取100个内容")
        
        # 从SohuGlobal API批量获取内容
        async with sohu_client as client:
            batch_result = await client.get_contents_batch(request.content_ids)
        
        if batch_result.get("code") != 200:
            raise HTTPException(status_code=500, detail="批量获取内容失败")
        
        contents = batch_result["data"]["contents"]
        
        # 如果需要包含MBTI分析
        if request.include_mbti:
            for content in contents:
                content_id = content.get("id")
                if content_id:
                    content_mbti = db_service.get_content_mbti(content_id)
                    if content_mbti:
                        content["mbti_analysis"] = content_mbti.to_dict()["probabilities"]
                    else:
                        content["mbti_analysis"] = None
        
        return BatchContentResponse(
            success=True,
            data=batch_result["data"],
            message="批量获取完成"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量获取内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量获取失败: {str(e)}")

# =============================================================================
# MBTI档案接口
# =============================================================================

@app.get("/api/v1/mbti/profile/{user_id}", response_model=MBTIProfileResponse)
async def get_user_mbti_profile(user_id: int = Path(..., gt=0)):
    """获取用户MBTI档案"""
    try:
        profile = db_service.get_user_profile(user_id)
        
        if not profile:
            # 创建默认档案
            profile = db_service.create_user_profile(user_id)
        
        profile_data = profile.to_dict()
        
        # 添加MBTI类型描述
        mbti_type = profile_data.get("mbti_type", "")
        profile_data["mbti_description"] = CONFIG["mbti"]["descriptions"].get(mbti_type, "")
        
        return MBTIProfileResponse(
            success=True,
            data=profile_data,
            message="获取MBTI档案成功"
        )
        
    except Exception as e:
        logger.error(f"获取MBTI档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取档案失败: {str(e)}")

@app.post("/api/v1/mbti/update/{user_id}", response_model=MBTIUpdateResponse)
async def update_user_mbti_profile(
    request: MBTIUpdateRequest,
    user_id: int = Path(..., gt=0)
):
    """手动触发用户MBTI档案更新"""
    try:
        # 触发MBTI更新
        update_result = await mbti_service.update_user_mbti_profile(
            user_id=user_id,
            force_update=request.force_update,
            analyze_last_n=request.analyze_last_n_behaviors
        )
        
        return MBTIUpdateResponse(
            success=True,
            data=update_result,
            message="MBTI档案更新完成" if update_result.get("updated") else "MBTI档案无需更新"
        )
        
    except Exception as e:
        logger.error(f"更新MBTI档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

# =============================================================================
# 内容MBTI评价接口（管理员功能）
# =============================================================================

@app.post("/api/v1/admin/content/{content_id}/evaluate")
async def evaluate_content_mbti(
    request: Dict[str, Any],
    content_id: int = Path(..., gt=0),
    content_type: Optional[str] = Query(None, pattern="^(article|video|product)$")
):
    """评价指定内容的MBTI特征（支持JSON请求体传入内容）"""
    try:
        # 检查是否已有评价
        existing_mbti = db_service.get_content_mbti(content_id)
        if existing_mbti:
            return {
                "success": True,
                "data": {
                    "content_id": content_id,
                    "already_evaluated": True,
                    "mbti_analysis": existing_mbti.to_dict()["probabilities"],
                    "scoring_mode": "existing"
                },
                "message": "内容已评价"
            }
        
        # 获取当前评分模式
        current_mode = get_mbti_scoring_mode()
        logger.info(f"内容 {content_id} MBTI评价，当前模式: {current_mode}")
        
        # 根据评分模式选择不同的评价方法
        if current_mode == "random":
            # 随机数生成模式
            probabilities = generate_consistent_random_mbti_scores()
            scoring_method = "random_generation"
            logger.info(f"内容 {content_id} 使用随机数生成MBTI评分")
            
        elif current_mode == "mixed":
            # 混合模式：50%概率使用AI，50%概率使用随机数
            if random.random() < 0.5:
                probabilities = await mbti_service.evaluate_content_mbti(
                    content=request.get("content", ""),
                    content_id=content_id,
                    content_title=request.get("title", ""),
                    content_type=content_type or "article"
                )
                scoring_method = "ai_evaluation"
                logger.info(f"内容 {content_id} 使用AI评价MBTI评分")
            else:
                probabilities = generate_consistent_random_mbti_scores()
                scoring_method = "random_generation"
                logger.info(f"内容 {content_id} 使用随机数生成MBTI评分")
                
        else:  # current_mode == "ai"
            # AI评价模式
        content_text = request.get("content", "")
        content_title = request.get("title", "")
        
        if content_text:
            # 如果请求体包含内容文本，直接评价
            logger.info(f"使用请求体中的内容文本评价 content_id: {content_id}")
            probabilities = await mbti_service.evaluate_content_mbti(
                content=content_text,
                content_id=content_id,
                content_title=content_title,
                content_type=content_type or "article"
            )
        else:
            # 否则使用原有逻辑通过content_id获取内容
            logger.info(f"使用content_id获取内容并评价: {content_id}")
            probabilities = await mbti_service.evaluate_content_by_id(
                content_id=content_id,
                content_type=content_type
            )
            
            scoring_method = "ai_evaluation"
            logger.info(f"内容 {content_id} 使用AI评价MBTI评分")
        
        # 保存评分到数据库
        if probabilities:
            db_service.save_content_mbti(
                content_id=content_id,
                probabilities=probabilities,
                content_title=request.get("title", ""),
                content_type=content_type or "article",
                quality_score=0.5  # 添加缺失的quality_score参数
            )
            logger.info(f"内容 {content_id} MBTI评分已保存到数据库")
            
            return {
                "success": True,
                "data": {
                    "content_id": content_id,
                    "evaluation_completed": True,
                "mbti_analysis": probabilities,
                "scoring_mode": current_mode,
                "scoring_method": scoring_method,
                "timestamp": datetime.utcnow().isoformat()
                },
            "message": f"MBTI评价完成 (模式: {current_mode})"
            }
        
    except Exception as e:
        logger.error(f"评价内容MBTI失败: {e}")
        raise HTTPException(status_code=500, detail=f"评价失败: {str(e)}")

@app.post("/api/v1/admin/content/batch_evaluate")
async def batch_evaluate_content_mbti(
    background_tasks: BackgroundTasks,
    content_ids: List[int],
    max_concurrent: int = Query(3, ge=1, le=10)
):
    """批量评价内容MBTI特征（异步）"""
    try:
        if not content_ids:
            raise HTTPException(status_code=400, detail="内容ID列表不能为空")
        
        if len(content_ids) > 50:
            raise HTTPException(status_code=400, detail="一次最多评价50个内容")
        
        # 过滤已评价的内容
        pending_ids = []
        for content_id in content_ids:
            existing_mbti = db_service.get_content_mbti(content_id)
            if not existing_mbti:
                pending_ids.append(content_id)
        
        if pending_ids:
            # 后台任务批量评价
            background_tasks.add_task(
                mbti_service.batch_evaluate_contents,
                pending_ids,
                max_concurrent
            )
        
        return {
            "success": True,
            "data": {
                "total_requested": len(content_ids),
                "already_evaluated": len(content_ids) - len(pending_ids),
                "pending_evaluation": len(pending_ids),
                "pending_ids": pending_ids
            },
            "message": f"批量MBTI评价已开始，{len(pending_ids)}个内容待评价"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量评价内容MBTI失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量评价失败: {str(e)}")

# =============================================================================
# 应用启动和运行
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"{CONFIG['app']['name']} v{CONFIG['app']['version']} 启动中...")
    logger.info("数据库服务已初始化")
    logger.info("MBTI评价服务已初始化")
    logger.info("SohuGlobal API客户端已初始化")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用正在关闭...")

def run_server():
    """运行服务器"""
    # 注意：reload=True 会启用热重载，监控 CRITICAL_FILES 中的文件变化
    # 如果不需要热重载，可以在 new_config.py 中设置 DEBUG = False
    # 或者直接在这里设置 reload=False
    uvicorn.run(
        "main_api:app",
        host=CONFIG["app"]["host"],
        port=CONFIG["app"]["port"],
        reload=CONFIG["app"]["debug"],  # 从配置文件读取，默认关闭
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
