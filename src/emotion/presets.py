"""预定义的情感配置"""

# GPT-SoVITS 情感预设
GPTSOVITS_EMOTION_PRESETS = {
    "neutral": {
        "name": "中性",
        "description": "标准播音风格，清晰平稳",
        "parameters": {
            "temperature": 0.3,
            "top_k": 3,
            "top_p": 0.7,
            "speed_factor": 1.0,
            "repetition_penalty": 1.35
        }
    },
    "emphasis": {
        "name": "强调",
        "description": "严肃正式，适合重要内容",
        "parameters": {
            "temperature": 0.2,
            "top_k": 2,
            "top_p": 0.5,
            "speed_factor": 0.9,
            "repetition_penalty": 1.4
        }
    },
    "friendly": {
        "name": "友好",
        "description": "活泼亲切，适合轻松内容",
        "parameters": {
            "temperature": 0.5,
            "top_k": 5,
            "top_p": 0.9,
            "speed_factor": 1.1,
            "repetition_penalty": 1.3
        }
    },
    "professional": {
        "name": "专业",
        "description": "商务正式，适合专业场合",
        "parameters": {
            "temperature": 0.25,
            "top_k": 3,
            "top_p": 0.6,
            "speed_factor": 0.95,
            "repetition_penalty": 1.35
        }
    },
    "storytelling": {
        "name": "讲故事",
        "description": "富有感情，适合叙事内容",
        "parameters": {
            "temperature": 0.6,
            "top_k": 6,
            "top_p": 0.85,
            "speed_factor": 0.95,
            "repetition_penalty": 1.25
        }
    },
    "news": {
        "name": "新闻播报",
        "description": "客观中立，节奏明快",
        "parameters": {
            "temperature": 0.2,
            "top_k": 2,
            "top_p": 0.6,
            "speed_factor": 1.05,
            "repetition_penalty": 1.4
        }
    }
}

# Gemini TTS 声音映射
GEMINI_VOICE_EMOTIONS = {
    "neutral": {
        "name": "中性",
        "voice_name": "Kore",
        "description": "清晰标准的声音"
    },
    "emphasis": {
        "name": "强调",
        "voice_name": "Charon",
        "description": "深沉严肃的声音"
    },
    "friendly": {
        "name": "友好",
        "voice_name": "Puck",
        "description": "活泼友好的声音"
    },
    "professional": {
        "name": "专业",
        "voice_name": "Vale",
        "description": "专业正式的声音"
    },
    "energetic": {
        "name": "活力",
        "voice_name": "Fenrir",
        "description": "充满活力的声音"
    },
    "calm": {
        "name": "平静",
        "voice_name": "Aoede",
        "description": "温柔平静的声音"
    }
}

# 情感组合建议
EMOTION_COMBINATIONS = {
    "documentary": {
        "name": "纪录片",
        "description": "适合纪录片配音",
        "sequence": [
            {"emotion": "professional", "usage": "开场和结尾"},
            {"emotion": "neutral", "usage": "主要叙述"},
            {"emotion": "emphasis", "usage": "重要信息"}
        ]
    },
    "tutorial": {
        "name": "教程",
        "description": "适合教学视频",
        "sequence": [
            {"emotion": "friendly", "usage": "开场问候"},
            {"emotion": "neutral", "usage": "步骤说明"},
            {"emotion": "emphasis", "usage": "重点提示"}
        ]
    },
    "advertisement": {
        "name": "广告",
        "description": "适合商业广告",
        "sequence": [
            {"emotion": "energetic", "usage": "吸引注意"},
            {"emotion": "friendly", "usage": "产品介绍"},
            {"emotion": "emphasis", "usage": "行动号召"}
        ]
    }
}

# 获取所有可用的情感列表
def get_all_emotions():
    """获取所有预定义的情感类型"""
    emotions = set()
    emotions.update(GPTSOVITS_EMOTION_PRESETS.keys())
    emotions.update(GEMINI_VOICE_EMOTIONS.keys())
    return sorted(list(emotions))

# 获取服务支持的情感
def get_service_emotions(service_name: str):
    """获取特定服务支持的情感类型"""
    if service_name == "gpt_sovits":
        return list(GPTSOVITS_EMOTION_PRESETS.keys())
    elif service_name == "gemini":
        return list(GEMINI_VOICE_EMOTIONS.keys())
    else:
        return get_all_emotions()