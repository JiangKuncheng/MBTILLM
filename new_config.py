# -*- coding: utf-8 -*-
"""
MBTI推荐系统配置文件
"""

import os
from typing import Dict, Any

# =============================================================================
# 基础配置
# =============================================================================

# 应用配置
APP_NAME = "MBTI推荐系统"
APP_VERSION = "1.0.0"
API_VERSION = "v1"

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"  # 从环境变量读取，默认关闭

# =============================================================================
# 数据库配置
# =============================================================================

# SQLite数据库配置
DATABASE_CONFIG = {
    "sqlite_path": "mbti_system.db",
    "echo": False,  # 是否打印SQL语句
    "pool_pre_ping": True,
}

# ChromaDB向量数据库配置
VECTOR_DB_CONFIG = {
    "persist_directory": "./chroma_db",
    "collection_name": "mbti_content_vectors",
    "embedding_function": "default",  # 使用默认的嵌入函数
}

# =============================================================================
# 外部API配置
# =============================================================================

# SiliconFlow LLM API配置
SILICONFLOW_CONFIG = {
    "api_key": "sk-ngeumocvbdfzaoqgldkwbkofkzyqcltfwbltcrkpoafbmxpb",
    "base_url": "https://api.siliconflow.cn/v1",
    "model": "Qwen/Qwen2.5-VL-32B-Instruct",  # 使用用户提供的可用模型
    "timeout": 600,
    "max_retries": 3,
}

# SohuGlobal API配置
SOHU_API_CONFIG = {
    "base_url": "http://192.168.150.252:8080",  
    "login_phone": "admin",
    "login_password": "U9xbHDJUH1pmx9hk7nXbQQ==",
    "timeout": 15,
    "max_retries": 2,
}

# =============================================================================
# MBTI评价配置
# =============================================================================

# MBTI维度定义
MBTI_DIMENSIONS = ["E", "I", "S", "N", "T", "F", "J", "P"]

# MBTI类型定义 
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP", 
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

# MBTI类型描述
MBTI_TYPE_DESCRIPTIONS = {
    "INTJ": "建筑师 - 富有想象力和战略性的思想家",
    "INTP": "逻辑学家 - 具有创造性的发明家",
    "ENTJ": "指挥官 - 大胆、富有想象力的强大领导者",
    "ENTP": "辩论家 - 聪明好奇的思想家",
    "INFJ": "提倡者 - 安静而神秘的鼓舞他人",
    "INFP": "调停者 - 诗意善良的利他主义者",
    "ENFJ": "主人公 - 富有魅力鼓舞他人的领导者",
    "ENFP": "竞选者 - 热情创造性的自由精神",
    "ISTJ": "物流师 - 实际事实的可靠工作者",
    "ISFJ": "守护者 - 非常专注的温暖保护者",
    "ESTJ": "总经理 - 优秀的管理者",
    "ESFJ": "执政官 - 极有同情心的受欢迎的人",
    "ISTP": "鉴赏家 - 大胆而实际的实验者",
    "ISFP": "探险家 - 灵活迷人的艺术家",
    "ESTP": "企业家 - 聪明、精力充沛的感知者",
    "ESFP": "表演者 - 自发的、精力充沛的娱乐者"
}

# MBTI评价提示词模板
MBTI_EVALUATION_PROMPT = """
你是一个专业的MBTI心理学专家。请根据以下内容列表，分析每个内容在MBTI四个维度上的倾向，并给出概率分布。

内容列表：
{contents}

请仔细分析每个内容，判断其在以下四个MBTI维度上的概率分布：

### 1. **E/I维度（外向/内向）**：
- **外向(E)**：表现出与他人交流、社交活动、外部世界互动的倾向
- **内向(I)**：表现出独处、内省、内在世界关注的倾向
- 要求：E + I = 1.0

### 2. **S/N维度（感觉/直觉）**：
- **感觉(S)**：关注具体细节、实际经验、现实情况
- **直觉(N)**：关注可能性、未来、抽象概念、潜在可能
- 要求：S + N = 1.0

### 3. **T/F维度（思维/情感）**：
- **思维(T)**：使用逻辑、客观分析、理性决策
- **情感(F)**：考虑他人感受、价值观、和谐关系、个人价值
- 要求：T + F = 1.0

### 4. **J/P维度（判断/知觉）**：
- **判断(J)**：表现出计划性、组织性、决断性
- **知觉(P)**：表现出灵活性、适应性、开放性
- 要求：J + P = 1.0

请返回JSON格式的结果，包含每个内容的MBTI分析：

```json
{{
  "results": [

    {{
      "content_id": 1002,
      "content_title": "内容标题2", 
      "mbti_probabilities": {{
        "E": 0.3, "I": 0.7, "S": 0.6, "N": 0.4, "T": 0.4, "F": 0.6, "J": 0.3, "P": 0.7
      }}
    }}
  ]
}}
```

返回正例：
{{
  "results": [
    {{
      "content_id": 1002,
      "content_title": "内容标题2", 
      "mbti_probabilities": {{
        "E": 0.3, "I": 0.7, "S": 0.6, "N": 0.4, "T": 0.4, "F": 0.6, "J": 0.3, "P": 0.7
      }}
    }}
  ]
}}
***json格式按要求输出，不要其他文字说明，只返回json，如果返回格式错误视为生成失败***



返回反例：
#### **3. ID: 3053**
**标题**: 张启山
**内容**: 同上，重复内容。
**分析**:
- **E（外向）**: 同上，分享美食教程，可能喜欢与他人交流。
- **I（内向）**: 同上，内容集中在个人体验和美食制作。
- **S（实感）**: 同上，强调实际的美食制作和品尝。
- **N（直觉）**: 同上，没有明显的抽象或未来导向的内容。
- **T（思考）**: 同上，更注重实际的制作过程和结果。
- **F（情感）**: 同上，有“好吃到嗦手指”的情感表达，但整体偏理性。
- **J（判断）**: 同上，内容结构清晰，有明确的教程和标签。
- **P（知觉）**: 同上，有一定的灵活性，分享个人体验。

**评分**:
```json
{
  "content_id": 3053,
  "mbti": {"E": 0.5, "I": 0.5, "S": 0.7, "N": 0.3, "T": 0.6, "F": 0.4, "J": .6, "P": 0.4}
}
输出了分析，影响后续json格式读取，所以属于反例

注意：
1. 每个维度的两个概率必须是0-1之间的小数，且总和必须等于1.0
2. 概率表示该内容倾向于某个特征的程度
3. 只返回JSON格式，不要其他文字说明，如果返回格式错误视为生成失败
4. 确保每对概率相加等于1.0：E+I=1.0, S+N=1.0, T+F=1.0, J+P=1.0
5. 返回格式必须包含results数组，每个元素包含content_id、content_title和mbti_probabilities
6. 一定要按要求返回JSON格式，不要其他文字说明
"""

# 批量MBTI评价提示词模板（简化版，用于大量内容）
BATCH_MBTI_EVALUATION_PROMPT = """
你是一个专业的MBTI心理学专家。请根据以下内容列表，分析每个内容在MBTI四个维度上的倾向，并给出概率分布。

内容列表：
{contents}

请仔细分析每个内容，判断其在以下四个MBTI维度上的概率分布：

### 1. **E/I维度（外向/内向）**：
- **外向(E)**：表现出与他人交流、社交活动、外部世界互动的倾向
- **内向(I)**：表现出独处、内省、内在世界关注的倾向
- 要求：E + I = 1.0

### 2. **S/N维度（感觉/直觉）**：
- **感觉(S)**：关注具体细节、实际经验、现实情况
- **直觉(N)**：关注可能性、未来、抽象概念、潜在可能
- 要求：S + N = 1.0

### 3. **T/F维度（思维/情感）**：
- **思维(T)**：使用逻辑、客观分析、理性决策
- **情感(F)**：考虑他人感受、价值观、和谐关系、个人价值
- 要求：T + F = 1.0

### 4. **J/P维度（判断/知觉）**：
- **判断(J)**：表现出计划性、组织性、决断性
- **知觉(P)**：表现出灵活性、适应性、开放性
- 要求：J + P = 1.0

请返回JSON格式的结果，包含每个内容的MBTI分析：

```json
{{
  "results": [

    {{
      "content_id": 1002,
      "content_title": "内容标题2", 
      "mbti_probabilities": {{
        "E": 0.3, "I": 0.7, "S": 0.6, "N": 0.4, "T": 0.4, "F": 0.6, "J": 0.3, "P": 0.7
      }}
    }}
  ]
}}
```

返回正例：
{{
  "results": [
    {{
      "content_id": 1002,
      "content_title": "内容标题2", 
      "mbti_probabilities": {{
        "E": 0.3, "I": 0.7, "S": 0.6, "N": 0.4, "T": 0.4, "F": 0.6, "J": 0.3, "P": 0.7
      }}
    }}
  ]
}}
***json格式按要求输出，不要其他文字说明，只返回json，如果返回格式错误视为生成失败***



返回反例：
#### **3. ID: 3053**
**标题**: 张启山
**内容**: 同上，重复内容。
**分析**:
- **E（外向）**: 同上，分享美食教程，可能喜欢与他人交流。
- **I（内向）**: 同上，内容集中在个人体验和美食制作。
- **S（实感）**: 同上，强调实际的美食制作和品尝。
- **N（直觉）**: 同上，没有明显的抽象或未来导向的内容。
- **T（思考）**: 同上，更注重实际的制作过程和结果。
- **F（情感）**: 同上，有“好吃到嗦手指”的情感表达，但整体偏理性。
- **J（判断）**: 同上，内容结构清晰，有明确的教程和标签。
- **P（知觉）**: 同上，有一定的灵活性，分享个人体验。

**评分**:
```json
{
  "content_id": 3053,
  "mbti": {"E": 0.5, "I": 0.5, "S": 0.7, "N": 0.3, "T": 0.6, "F": 0.4, "J": .6, "P": 0.4}
}
输出了分析，影响后续json格式读取，所以属于反例

注意：
1. 每个维度的两个概率必须是0-1之间的小数，且总和必须等于1.0
2. 概率表示该内容倾向于某个特征的程度
3. 只返回JSON格式，不要其他文字说明，如果返回格式错误视为生成失败
4. 确保每对概率相加等于1.0：E+I=1.0, S+N=1.0, T+F=1.0, J+P=1.0
5. 返回格式必须包含results数组，每个元素包含content_id、content_title和mbti_probabilities
6. 一定要按要求返回JSON格式，不要其他文字说明
"""

# =============================================================================
# 推荐算法配置
# =============================================================================

# 推荐算法参数
RECOMMENDATION_CONFIG = {
    # 默认推荐数量
    "default_limit": 50,
    "max_limit": 100,
    
    # 相似度计算
    "default_similarity_threshold": 0.5,
    "min_similarity_threshold": 0.1,
    "max_similarity_threshold": 0.9,
    
    # 内容过滤
    "default_fresh_days": 30,
    "max_fresh_days": 365,
    "exclude_viewed_default": True,
    
    # 缓存配置
    "cache_ttl": 1800,  # 30分钟
    "user_profile_cache_ttl": 3600,  # 1小时
    
    # 算法权重
    "mbti_similarity_weight": 0.6,
    "content_quality_weight": 0.3,
    "personal_preference_weight": 0.1,
}

# =============================================================================
# 用户行为配置
# =============================================================================

# 行为类型权重配置
BEHAVIOR_WEIGHTS = {
    "view": 0.1,        # 浏览
    "like": 0.8,        # 点赞
    "collect": 0.9,     # 收藏
    "comment": 0.7,     # 评论
    "share": 0.6,       # 分享
    "follow": 0.6,      # 关注
}

# MBTI更新配置
MBTI_UPDATE_CONFIG = {
    # 触发MBTI重新计算的行为数量阈值
    "behavior_threshold": 50,
    
    # MBTI更新时的权重配置
    "history_weight": 0.7,     # 历史MBTI评分权重
    "new_analysis_weight": 0.3, # 新分析结果权重
    
    # 最小行为数量要求
    "min_behaviors_for_analysis": 10,
    
    # 分析时考虑的最大行为数量
    "max_behaviors_for_analysis": 200,
    
    # 批量评价配置
    "batch_evaluation_size": 10,  # 每次批量评价的内容数量
    "max_concurrent_evaluations": 3,  # 最大并发评价数
    "evaluation_timeout": 60,  # 评价超时时间（秒）
}

# =============================================================================
# 日志配置
# =============================================================================

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_path": "logs/mbti_recommendation.log",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# =============================================================================
# 安全配置
# =============================================================================

# JWT配置
JWT_CONFIG = {
    "secret_key": "your-super-secret-jwt-key-change-in-production",
    "algorithm": "HS256",
    "access_token_expire_minutes": 60 * 24,  # 24小时
}

# API限流配置
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 100,
    "requests_per_hour": 1000,
    "burst_size": 20,
}

# =============================================================================
# 开发/生产环境配置
# =============================================================================

# 从环境变量获取配置（生产环境覆盖）
def get_config() -> Dict[str, Any]:
    """获取配置，支持环境变量覆盖"""
    config = {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "api_version": API_VERSION,
            "host": os.getenv("HOST", HOST),
            "port": int(os.getenv("PORT", PORT)),
            "debug": os.getenv("DEBUG", str(DEBUG)).lower() == "true",
        },
        "database": DATABASE_CONFIG,
        "vector_db": VECTOR_DB_CONFIG,
        "siliconflow": {
            **SILICONFLOW_CONFIG,
            "api_key": os.getenv("SILICONFLOW_API_KEY", SILICONFLOW_CONFIG["api_key"])
        },
        "sohu_api": SOHU_API_CONFIG,
        "mbti": {
            "dimensions": MBTI_DIMENSIONS,
            "types": MBTI_TYPES,
            "descriptions": MBTI_TYPE_DESCRIPTIONS,
            "evaluation_prompt": MBTI_EVALUATION_PROMPT,
            "batch_evaluation_prompt": BATCH_MBTI_EVALUATION_PROMPT,
            
            # 批量评价配置
            "batch_size": 10,  # 每次批量评价的内容数量
            "max_batch_size": 20,  # 最大批量大小
            "concurrent_batches": 3,  # 并发处理的批次数
        },
        "recommendation": RECOMMENDATION_CONFIG,
        "behavior": {
            "weights": BEHAVIOR_WEIGHTS,
            "mbti_update": MBTI_UPDATE_CONFIG,
        },
        "logging": LOGGING_CONFIG,
        "jwt": {
            **JWT_CONFIG,
            "secret_key": os.getenv("JWT_SECRET_KEY", JWT_CONFIG["secret_key"])
        },
        "rate_limit": RATE_LIMIT_CONFIG,
    }
    
    return config

# 导出配置实例
CONFIG = get_config()
