# MBTI智能推荐系统

基于MBTI人格特征分析的智能内容推荐系统，通过分析用户行为和内容特征实现个性化推荐。

## 🚀 项目概述

### 核心功能

1. **用户行为追踪**: 记录用户点赞、收藏、评论等操作
2. **MBTI特征分析**: 使用LLM分析内容和用户的MBTI特征
3. **智能推荐算法**: 基于MBTI相似度的内容推荐
4. **动态学习机制**: 根据用户行为动态调整MBTI档案
5. **内容代理服务**: 集成SohuGlobal API获取内容详情

### 技术架构

- **后端框架**: FastAPI + Uvicorn
- **数据库**: SQLite (关系数据) 
- **AI服务**: SiliconFlow API (MBTI分析)
- **外部API**: SohuGlobal API (内容获取)
- **算法**: 余弦相似度匹配
- **并发**: asyncio + aiohttp

## 📦 安装部署

### 1. 环境要求

- Python 3.8+
- 8GB+ 内存
- 网络连接 (访问AI和内容API)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置文件

编辑 `new_config.py` 中的配置：

```python
# SiliconFlow LLM API配置
SILICONFLOW_CONFIG = {
    "api_key": "your-api-key-here",  # 替换为你的API密钥
    # ... 其他配置
}

# SohuGlobal API配置  
SOHU_API_CONFIG = {
    "base_url": "https://api.sohuglobal.com",
    "login_phone": "your-phone",      # 替换为你的登录信息
    "login_password": "your-password", # 替换为你的密码
    # ... 其他配置
}
```

### 4. 启动服务

```bash
# 运行测试验证系统
python test_new_system.py

# 启动API服务
python main_api.py
```

服务启动后访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 🛠️ API接口说明

### 核心接口

#### 1. 记录用户行为
```bash
POST /api/v1/behavior/record
Content-Type: application/json

{
  "user_id": 123,
  "content_id": 1001,
  "action": "like",
  "source": "recommendation"
}
```

#### 2. 获取用户历史
```bash
GET /api/v1/behavior/history/123?limit=50&action=like
```

#### 3. 获取个性化推荐
```bash
GET /api/v1/recommendations/123?limit=50&content_type=article&similarity_threshold=0.6
```

#### 4. 获取内容详情
```bash
GET /api/v1/content/1001?include_mbti=true
```

#### 5. 批量获取内容
```bash
POST /api/v1/content/batch
Content-Type: application/json

{
  "content_ids": [1001, 1002, 1003],
  "include_mbti": true
}
```

### MBTI档案管理

#### 获取用户MBTI档案
```bash
GET /api/v1/mbti/profile/123
```

#### 手动更新MBTI档案
```bash
POST /api/v1/mbti/update/123
Content-Type: application/json

{
  "force_update": true,
  "analyze_last_n_behaviors": 100
}
```

## 🎯 使用流程

### 前端集成步骤

1. **记录用户行为**
   ```javascript
   // 用户点赞时
   fetch('/api/v1/behavior/record', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       user_id: 123,
       content_id: 1001,
       action: 'like'
     })
   });
   ```

2. **获取推荐内容**
   ```javascript
   // 获取推荐的content_id列表
   const response = await fetch('/api/v1/recommendations/123?limit=50');
   const data = await response.json();
   const contentIds = data.data.recommendations.map(r => r.content_id);
   ```

3. **获取内容详情**
   ```javascript
   // 批量获取内容详情
   const detailResponse = await fetch('/api/v1/content/batch', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       content_ids: contentIds,
       include_mbti: true
     })
   });
   ```

### 推荐算法工作原理

1. **用户行为收集**: 记录点赞、收藏等操作
2. **内容MBTI分析**: LLM分析内容的MBTI特征概率
3. **用户MBTI推断**: 基于用户行为分析用户MBTI特征
4. **相似度计算**: 使用余弦相似度匹配用户和内容
5. **动态更新**: 用户行为达到50个阈值时更新MBTI档案

## 📊 数据库设计

### 核心表结构

1. **user_profiles**: 用户MBTI档案
   - MBTI概率分布 (E,I,S,N,T,F,J,P)
   - 推导的MBTI类型
   - 置信度评分

2. **user_behaviors**: 用户行为记录
   - 行为类型、权重
   - 时间戳、来源

3. **content_mbti**: 内容MBTI特征
   - 内容的MBTI概率向量
   - 评价版本、质量分数

4. **recommendation_logs**: 推荐日志
   - 推荐结果、算法参数
   - 用户MBTI快照

## 🔧 配置说明

### MBTI更新策略

```python
MBTI_UPDATE_CONFIG = {
    "behavior_threshold": 50,        # 触发更新的行为数量
    "history_weight": 0.7,          # 历史评分权重
    "new_analysis_weight": 0.3,     # 新分析权重
    "min_behaviors_for_analysis": 10, # 最小分析行为数
}
```

### 推荐算法参数

```python
RECOMMENDATION_CONFIG = {
    "default_similarity_threshold": 0.5,  # 默认相似度阈值
    "mbti_similarity_weight": 0.6,        # MBTI权重
    "content_quality_weight": 0.3,        # 内容质量权重  
    "personal_preference_weight": 0.1,    # 个人偏好权重
}
```

### 行为权重配置

```python
BEHAVIOR_WEIGHTS = {
    "view": 0.1,        # 浏览
    "like": 0.8,        # 点赞
    "collect": 0.9,     # 收藏
    "comment": 0.7,     # 评论
    "share": 0.6,       # 分享
}
```

## 🧪 测试验证

### 运行测试

```bash
# 完整系统测试
python test_new_system.py

# 测试内容包括：
# 1. 数据库服务测试
# 2. MBTI评价服务测试  
# 3. SohuGlobal API测试
# 4. 推荐算法测试
# 5. MBTI档案更新测试
# 6. API调用模拟测试
```

### 测试输出示例

```
✅ 模块导入成功
✅ 创建用户档案: 12345
✅ 记录用户行为: like
✅ 用户行为统计: 1 个行为
✅ 内容MBTI评价完成:
    E: 0.750    I: 0.250
    S: 0.400    N: 0.600
    T: 0.300    F: 0.700
    J: 0.500    P: 0.500
✅ 生成推荐: 3 个内容，用户类型: ENFP
✅ MBTI档案更新: 无 -> ENFP
```

## 🚨 注意事项

### 1. API限制

- SiliconFlow API有调用频率限制
- SohuGlobal API需要有效的登录凭据
- 建议设置合理的并发限制

### 2. 性能优化

- 启用MBTI评价结果缓存
- 推荐结果缓存30分钟
- 批量处理时控制并发数量

### 3. 数据安全

- 用户只能访问自己的行为数据
- API接口需要适当的认证机制
- 敏感配置信息不要硬编码

### 4. 错误处理

- 网络异常时使用默认MBTI值
- API调用失败时有优雅降级
- 记录详细的错误日志便于调试

## 📈 性能指标

- **推荐响应时间**: < 500ms
- **行为记录响应时间**: < 100ms
- **MBTI评价时间**: 2-5秒 (依赖LLM API)
- **并发支持**: 1000+ QPS
- **数据库性能**: SQLite适合中小规模应用

## 🛣️ 扩展计划

### 短期优化

1. 添加Redis缓存层
2. 实现JWT用户认证
3. 添加API限流机制
4. 优化推荐算法参数

### 长期规划

1. 支持MySQL/PostgreSQL
2. 添加向量数据库(ChromaDB)
3. 实现更复杂的推荐算法
4. 添加A/B测试框架
5. 支持多租户架构

## 📞 支持与反馈

如有问题或建议，请提交Issue或联系开发团队。

---

**项目版本**: v1.0.0  
**最后更新**: 2024-01-20  
**开发团队**: MBTI推荐系统团队
