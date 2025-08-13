# MBTI用户推荐系统 API接口文档

## 概述

基于MBTI特征分析的智能内容推荐系统，通过分析用户行为和内容特征实现个性化推荐。

### 基础信息
- **基础URL**: `https://your-domain.com/api/v1`
- **认证方式**: JWT Token
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 1. 用户行为管理接口

### 1.1 记录用户行为

**接口**: `POST /behavior/record`

**描述**: 记录用户对内容的交互行为（点赞、收藏等）

#### 请求参数

```json
{
  "user_id": 123,
  "content_id": 1001,
  "action": "like",
  "timestamp": "2024-01-20T14:30:00Z",
  "source": "recommendation",
  "session_id": "sess_abc123"
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |
| content_id | integer | 是 | 内容ID |
| action | string | 是 | 操作类型: like, collect, comment, share, view |
| timestamp | string | 否 | 操作时间(ISO 8601格式) |
| source | string | 否 | 来源: recommendation, search, trending |
| session_id | string | 否 | 会话ID |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "behavior_id": 98765,
    "user_id": 123,
    "content_id": 1001,
    "action": "like",
    "recorded_at": "2024-01-20T14:30:00Z",
    "weight": 0.8,
    "mbti_update_triggered": false,
    "next_update_threshold": 35
  },
  "message": "行为记录成功"
}
```

### 1.2 获取用户行为历史

**接口**: `GET /behavior/history/{user_id}`

**描述**: 获取用户的历史操作记录

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID (路径参数) |
| action | string | 否 | 操作类型过滤 |
| limit | integer | 否 | 返回数量限制 (默认50，最大100) |
| offset | integer | 否 | 偏移量 (默认0) |
| start_date | string | 否 | 开始日期 (ISO 8601) |
| end_date | string | 否 | 结束日期 (ISO 8601) |

#### 请求示例

```
GET /behavior/history/123?action=like&limit=20&offset=0&start_date=2024-01-01T00:00:00Z
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "total_count": 156,
    "returned_count": 20,
    "behaviors": [
      {
        "behavior_id": 98765,
        "content_id": 1001,
        "action": "like",
        "timestamp": "2024-01-20T14:30:00Z",
        "weight": 0.8,
        "source": "recommendation"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 8,
      "has_next": true
    }
  }
}
```

### 1.3 获取用户行为统计

**接口**: `GET /behavior/stats/{user_id}`

**描述**: 获取用户行为统计信息

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "total_behaviors": 156,
    "last_30_days": 45,
    "action_distribution": {
      "like": 78,
      "collect": 31,
      "comment": 23,
      "share": 12,
      "view": 456
    },
    "activity_level": "高度活跃",
    "last_activity": "2024-01-20T14:30:00Z",
    "behaviors_since_last_mbti_update": 25
  }
}
```

---

## 2. 推荐服务接口

### 2.1 获取个性化推荐

**接口**: `GET /recommendations/{user_id}`

**描述**: 基于用户MBTI特征获取个性化内容推荐

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID (路径参数) |
| limit | integer | 否 | 推荐数量 (默认50，最大100) |
| content_type | string | 否 | 内容类型: article, video, product, all |
| similarity_threshold | float | 否 | 相似度阈值 (0.0-1.0，默认0.5) |
| exclude_viewed | boolean | 否 | 是否排除已浏览 (默认true) |
| fresh_days | integer | 否 | 只推荐最近N天内容 (默认30) |

#### 请求示例

```
GET /recommendations/123?limit=50&content_type=article&similarity_threshold=0.6
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "user_mbti_type": "ENFP",
    "user_mbti_probabilities": {
      "E": 0.7, "I": 0.3,
      "S": 0.4, "N": 0.6,
      "T": 0.3, "F": 0.7,
      "J": 0.4, "P": 0.6
    },
    "recommendations": [
      {
        "content_id": 1001,
        "similarity_score": 0.92,
        "mbti_match_traits": ["E", "N", "F", "P"],
        "rank": 1,
        "estimated_engagement": 0.87
      }
    ],
    "metadata": {
      "total_candidates": 1247,
      "filtered_count": 50,
      "avg_similarity": 0.78,
      "generation_time": "2024-01-20T14:30:00Z",
      "algorithm_version": "v1.2",
      "cache_hit": false
    }
  }
}
```

### 2.2 获取相似内容推荐

**接口**: `GET /recommendations/similar/{content_id}`

**描述**: 基于指定内容推荐相似内容

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content_id | integer | 是 | 内容ID (路径参数) |
| limit | integer | 否 | 推荐数量 (默认10) |
| user_id | integer | 否 | 用户ID (用于个性化调整) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "base_content_id": 1001,
    "base_mbti_vector": [0.8, 0.2, 0.4, 0.6, 0.3, 0.7, 0.4, 0.6],
    "similar_contents": [
      {
        "content_id": 1025,
        "similarity_score": 0.89,
        "mbti_distance": 0.11,
        "rank": 1
      }
    ]
  }
}
```

---

## 3. 内容服务接口

### 3.1 获取内容详情 (代理接口)

**接口**: `GET /content/{content_id}`

**描述**: 获取内容详细信息（代理到SohuGlobal API）

#### 响应示例

```json
{
  "success": true,
  "data": {
    "content_id": 1001,
    "title": "创意思维与团队协作的艺术",
    "content": "内容正文...",
    "content_type": "article",
    "author": "创意专家",
    "publish_time": "2024-01-15T10:30:00Z",
    "category": "职场技能",
    "view_count": 1250,
    "praise_count": 89,
    "comment_count": 23,
    "collect_count": 45,
    "mbti_analysis": {
      "E": 0.8, "I": 0.2,
      "S": 0.4, "N": 0.6,
      "T": 0.3, "F": 0.7,
      "J": 0.4, "P": 0.6
    },
    "source": "sohuglobal"
  }
}
```

### 3.2 批量获取内容

**接口**: `POST /content/batch`

**描述**: 批量获取多个内容的详细信息

#### 请求参数

```json
{
  "content_ids": [1001, 1002, 1003, 1004],
  "include_mbti": true
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "contents": [
      {
        "content_id": 1001,
        "title": "创意思维与团队协作的艺术",
        "content_type": "article",
        "mbti_analysis": {
          "E": 0.8, "I": 0.2,
          "S": 0.4, "N": 0.6,
          "T": 0.3, "F": 0.7,
          "J": 0.4, "P": 0.6
        }
      }
    ],
    "total_requested": 4,
    "total_found": 3,
    "missing_ids": [1004]
  }
}
```

---

## 4. MBTI档案接口

### 4.1 获取用户MBTI档案

**接口**: `GET /mbti/profile/{user_id}`

**描述**: 获取用户的MBTI概率分布档案

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "mbti_type": "ENFP",
    "probabilities": {
      "E": 0.7, "I": 0.3,
      "S": 0.4, "N": 0.6,
      "T": 0.3, "F": 0.7,
      "J": 0.4, "P": 0.6
    },
    "confidence_scores": {
      "E_I": 0.4,
      "S_N": 0.2,
      "T_F": 0.4,
      "J_P": 0.2
    },
    "last_updated": "2024-01-20T14:30:00Z",
    "total_behaviors_analyzed": 156,
    "analysis_history": [
      {
        "update_date": "2024-01-20T14:30:00Z",
        "trigger_reason": "50_behaviors_threshold",
        "behaviors_analyzed": 50
      }
    ]
  }
}
```

### 4.2 手动触发MBTI更新

**接口**: `POST /mbti/update/{user_id}`

**描述**: 手动触发用户MBTI评分更新

#### 请求参数

```json
{
  "force_update": true,
  "analyze_last_n_behaviors": 100
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "update_triggered": true,
    "behaviors_analyzed": 50,
    "old_mbti_type": "ENFP",
    "new_mbti_type": "ENFP",
    "probability_changes": {
      "E": {"old": 0.7, "new": 0.72, "change": 0.02},
      "N": {"old": 0.6, "new": 0.62, "change": 0.02}
    },
    "update_time": "2024-01-20T14:30:00Z"
  }
}
```

---

## 5. SohuGlobal API 内容获取文档

### 5.1 API基础信息

- **基础URL**: `https://api.sohuglobal.com`
- **认证方式**: 电话号码 + 密码登录获取Token
- **当前认证信息**:
  - 电话: `admin`
  - 密码: `U9xbHDJUH1pmx9hk7nXbQQ==`

### 5.2 登录获取Token

**接口**: `POST https://api.sohuglobal.com/api/user/login`

#### 请求参数

```json
{
  "phone": "admin",
  "password": "U9xbHDJUH1pmx9hk7nXbQQ=="
}
```

#### 响应示例

```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "id": 1,
      "phone": "admin",
      "nickname": "管理员"
    }
  }
}
```

### 5.3 获取文章内容

**接口**: `GET https://api.sohuglobal.com/api/article/list`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码 (默认1) |
| size | integer | 否 | 每页数量 (默认10) |
| keyword | string | 否 | 关键词搜索 |
| categoryId | integer | 否 | 分类ID |

#### 请求头

```
Authorization: Bearer {token}
```

#### 响应示例

```json
{
  "code": 200,
  "msg": "获取成功",
  "data": {
    "list": [
      {
        "id": 1001,
        "title": "创意思维与团队协作的艺术",
        "content": "在现代职场中，创意思维和团队协作...",
        "description": "探讨创意思维在团队中的应用",
        "author": "创意专家李明",
        "categoryId": 5,
        "categoryName": "职场技能",
        "viewCount": 1250,
        "praiseCount": 89,
        "commentCount": 23,
        "collectCount": 45,
        "publishTime": "2024-01-15T10:30:00Z",
        "updateTime": "2024-01-15T10:30:00Z",
        "status": 1
      }
    ],
    "total": 1247,
    "page": 1,
    "size": 10,
    "pages": 125
  }
}
```

### 5.4 获取单个文章详情

**接口**: `GET https://api.sohuglobal.com/api/article/{id}`

#### 响应示例

```json
{
  "code": 200,
  "msg": "获取成功",
  "data": {
    "id": 1001,
    "title": "创意思维与团队协作的艺术",
    "content": "完整的文章内容...",
    "description": "文章描述",
    "author": "创意专家李明",
    "categoryId": 5,
    "categoryName": "职场技能",
    "tags": ["创意", "团队", "协作"],
    "viewCount": 1250,
    "praiseCount": 89,
    "commentCount": 23,
    "collectCount": 45,
    "publishTime": "2024-01-15T10:30:00Z",
    "updateTime": "2024-01-15T10:30:00Z"
  }
}
```

### 5.5 获取视频内容

**接口**: `GET https://api.sohuglobal.com/api/video/list`

#### 请求参数

同文章接口，支持分页和搜索

#### 响应示例

```json
{
  "code": 200,
  "msg": "获取成功",
  "data": {
    "list": [
      {
        "id": 2001,
        "title": "团队沟通技巧视频教程",
        "description": "如何在团队中进行有效沟通",
        "videoUrl": "https://video.example.com/team-communication.mp4",
        "coverImage": "https://img.example.com/cover.jpg",
        "duration": 1280,
        "author": "沟通专家王老师",
        "categoryId": 3,
        "categoryName": "技能培训",
        "viewCount": 2340,
        "praiseCount": 156,
        "commentCount": 89,
        "publishTime": "2024-01-14T15:20:00Z"
      }
    ],
    "total": 456,
    "page": 1,
    "size": 10
  }
}
```

### 5.6 获取商品信息

**接口**: `GET https://api.sohuglobal.com/api/product/list`

#### 响应示例

```json
{
  "code": 200,
  "msg": "获取成功",
  "data": {
    "list": [
      {
        "id": 3001,
        "title": "《高效团队管理手册》",
        "description": "团队管理实用指南",
        "price": 89.00,
        "originalPrice": 120.00,
        "image": "https://img.example.com/book.jpg",
        "author": "管理专家张三",
        "categoryId": 7,
        "categoryName": "管理书籍",
        "stock": 100,
        "salesCount": 234,
        "rating": 4.8,
        "publishTime": "2024-01-10T09:00:00Z"
      }
    ],
    "total": 89,
    "page": 1,
    "size": 10
  }
}
```

---

## 6. 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未授权/Token无效 |
| 403 | 403 | 禁止访问 |
| 404 | 404 | 资源不存在 |
| 429 | 429 | 请求频率超限 |
| 500 | 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "success": false,
  "error_code": "USER_NOT_FOUND",
  "message": "用户不存在",
  "details": {
    "user_id": 123,
    "timestamp": "2024-01-20T14:30:00Z"
  }
}
```

---

## 7. 调用示例

### Python调用示例

```python
import requests

# 1. 记录用户行为
behavior_data = {
    "user_id": 123,
    "content_id": 1001,
    "action": "like"
}
response = requests.post(
    "https://your-domain.com/api/v1/behavior/record",
    headers={"Authorization": "Bearer your_token"},
    json=behavior_data
)

# 2. 获取推荐
response = requests.get(
    "https://your-domain.com/api/v1/recommendations/123?limit=50",
    headers={"Authorization": "Bearer your_token"}
)
recommendations = response.json()["data"]["recommendations"]

# 3. 获取内容详情 (只需要content_id)
content_ids = [rec["content_id"] for rec in recommendations]
for content_id in content_ids:
    response = requests.get(
        f"https://your-domain.com/api/v1/content/{content_id}",
        headers={"Authorization": "Bearer your_token"}
    )
    content_detail = response.json()["data"]
```

### JavaScript调用示例

```javascript
// 记录点赞行为
async function recordLike(userId, contentId) {
  const response = await fetch('/api/v1/behavior/record', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer your_token',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: userId,
      content_id: contentId,
      action: 'like'
    })
  });
  return response.json();
}

// 获取推荐内容
async function getRecommendations(userId, limit = 50) {
  const response = await fetch(`/api/v1/recommendations/${userId}?limit=${limit}`, {
    headers: {
      'Authorization': 'Bearer your_token'
    }
  });
  return response.json();
}

// 获取用户历史
async function getUserHistory(userId, limit = 50) {
  const response = await fetch(`/api/v1/behavior/history/${userId}?limit=${limit}`, {
    headers: {
      'Authorization': 'Bearer your_token'
    }
  });
  return response.json();
}
```

---

## 8. 性能指标

- **推荐接口响应时间**: < 500ms
- **行为记录响应时间**: < 100ms  
- **历史查询响应时间**: < 200ms
- **并发支持**: 1000+ QPS
- **缓存命中率**: > 80%

---

## 9. 版本信息

- **当前版本**: v1.0
- **API版本**: v1
- **最后更新**: 2024-01-20
- **向后兼容**: 90天
