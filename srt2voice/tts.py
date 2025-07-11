"""
OpenAI TTS集成模块
负责调用OpenAI的文字转语音API
"""

from openai import OpenAI
from typing import Tuple, Optional
from .utils import retry_on_error


class TTSGenerator:
    """TTS语音生成器"""
    
    # 支持的语音类型
    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    # TTS模型
    MODELS = {
        "tts-1": 0.015,      # $0.015 per 1000 characters
        "tts-1-hd": 0.030    # $0.030 per 1000 characters
    }
    
    def __init__(self, api_key: str, model: str = "tts-1-hd"):
        """
        初始化TTS生成器
        
        Args:
            api_key: OpenAI API密钥
            model: TTS模型选择 (tts-1 或 tts-1-hd)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.char_count = 0
        self.price_per_1k = self.MODELS.get(model, 0.030)
        
    @retry_on_error(max_retries=3, delay=2)
    def generate_speech(self, text: str, voice: str = "alloy", speed: float = 1.0) -> Tuple[bytes, float]:
        """
        生成语音并返回音频数据和费用
        
        Args:
            text: 要转换的文本
            voice: 语音类型
            speed: 语速 (0.25-4.0)
            
        Returns:
            (音频数据, 本次费用)
        """
        # 验证参数
        if voice not in self.VOICES:
            raise ValueError(f"不支持的语音类型: {voice}")
        
        if not 0.25 <= speed <= 4.0:
            raise ValueError(f"语速必须在0.25-4.0之间: {speed}")
        
        # 文本预处理
        text = text.strip()
        if not text:
            raise ValueError("文本不能为空")
        
        # 计算字符数
        char_count = len(text)
        self.char_count += char_count
        
        try:
            # 调用OpenAI TTS API
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed
            )
            
            # 计算本次费用
            cost = (char_count / 1000) * self.price_per_1k
            
            # 返回音频内容和费用
            return response.content, cost
            
        except Exception as e:
            raise Exception(f"TTS生成失败: {e}")
    
    def get_total_cost(self) -> float:
        """获取总费用"""
        return (self.char_count / 1000) * self.price_per_1k
    
    def estimate_cost(self, char_count: int) -> float:
        """
        估算费用
        
        Args:
            char_count: 字符数
            
        Returns:
            预估费用（美元）
        """
        return (char_count / 1000) * self.price_per_1k
    
    def reset_counter(self):
        """重置计数器"""
        self.char_count = 0