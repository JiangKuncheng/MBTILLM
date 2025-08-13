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

# 配置日志
logging.basicConfig(
    level=getattr(logging, CONFIG["logging"]["level"]),
    format=CONFIG["logging"]["format"]
)
logger = logging.getLogger(__name__)

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
            "timestamp": datetime.utcnow().isoformat()
        }
    }

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
        
        # 检查是否需要触发MBTI更新
        mbti_update_triggered = False
        threshold = CONFIG["behavior"]["mbti_update"]["behavior_threshold"]
        next_update_threshold = threshold - behavior_count
        
        if behavior_count >= threshold:
            # 后台任务更新MBTI档案
            background_tasks.add_task(
                mbti_service.update_user_mbti_profile,
                request.user_id,
                False  # 不强制更新
            )
            mbti_update_triggered = True
            next_update_threshold = threshold
        
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
    limit: int = Query(50, ge=1, le=100),
    content_type: Optional[str] = Query(None, pattern="^(article|video|product|all)$"),
    similarity_threshold: float = Query(0.5, ge=0.1, le=0.9),
    exclude_viewed: bool = Query(True),
    fresh_days: int = Query(30, ge=1, le=365)
):
    """获取用户个性化推荐"""
    try:
        # 生成推荐
        recommendations = db_service.get_recommendations_for_user(
            user_id=user_id,
            limit=limit,
            content_type=content_type,
            similarity_threshold=similarity_threshold,
            exclude_viewed=exclude_viewed,
            fresh_days=fresh_days
        )
        
        logger.info(f"为用户 {user_id} 生成 {len(recommendations['recommendations'])} 个推荐")
        
        return RecommendationResponse(
            success=True,
            data=recommendations,
            message="推荐生成成功"
        )
        
    except Exception as e:
        logger.error(f"生成推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"推荐生成失败: {str(e)}")

@app.get("/api/v1/recommendations/similar/{content_id}")
async def get_similar_content_recommendations(
    content_id: int = Path(..., gt=0),
    limit: int = Query(10, ge=1, le=50),
    user_id: Optional[int] = Query(None, gt=0)
):
    """获取相似内容推荐"""
    try:
        # 获取基础内容的MBTI特征
        base_content_mbti = db_service.get_content_mbti(content_id)
        if not base_content_mbti:
            raise HTTPException(status_code=404, detail="内容MBTI特征不存在")
        
        # 获取候选内容
        candidate_contents = db_service.get_contents_for_recommendation(limit=500)
        
        if not candidate_contents:
            return {
                "success": True,
                "data": {
                    "base_content_id": content_id,
                    "base_mbti_vector": base_content_mbti.get_vector(),
                    "similar_contents": []
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
        
        # 设置排名并限制数量
        for i, content in enumerate(similar_contents[:limit]):
            content["rank"] = i + 1
        
        similar_contents = similar_contents[:limit]
        
        return {
            "success": True,
            "data": {
                "base_content_id": content_id,
                "base_mbti_vector": base_vector,
                "similar_contents": similar_contents
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
                    "mbti_analysis": existing_mbti.to_dict()["probabilities"]
                },
                "message": "内容已评价"
            }
        
        # 从请求体获取内容文本
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
            
            return {
                "success": True,
                "data": {
                    "content_id": content_id,
                    "evaluation_completed": True,
                    "mbti_analysis": probabilities
                },
                "message": "MBTI评价完成"
            }
        else:
            # 否则使用原有逻辑通过content_id获取内容
            logger.info(f"使用content_id获取内容并评价: {content_id}")
            probabilities = await mbti_service.evaluate_content_by_id(
                content_id=content_id,
                content_type=content_type
            )
            
            return {
                "success": True,
                "data": {
                    "content_id": content_id,
                    "evaluation_completed": True,
                    "mbti_analysis": probabilities
                },
                "message": "MBTI评价完成"
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
    uvicorn.run(
        "main_api:app",
        host=CONFIG["app"]["host"],
        port=CONFIG["app"]["port"],
        reload=CONFIG["app"]["debug"],
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
