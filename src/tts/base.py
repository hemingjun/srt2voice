"""TTS服务抽象基类"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydub import AudioSegment

from ..cache.manager import get_cache


class TTSService(ABC):
    """TTS服务抽象基类"""
    
    def __init__(self, config: dict):
        """初始化TTS服务
        
        Args:
            config: 服务配置字典
        """
        self.config = config
        self.service_name = config.get('service_name', self.__class__.__name__)
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> None:
        """验证配置有效性"""
        pass
    
    @abstractmethod
    def text_to_speech(self, text: str, emotion: Optional[str] = None) -> AudioSegment:
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            emotion: 可选的情感参数
            
        Returns:
            AudioSegment: 音频片段
        """
        pass
    
    def batch_text_to_speech(self, texts: List[str]) -> List[AudioSegment]:
        """批量转换文本为语音
        
        Args:
            texts: 文本列表
            
        Returns:
            List[AudioSegment]: 音频片段列表
        """
        return [self.text_to_speech(text) for text in texts]
    
    def check_health(self) -> bool:
        """检查服务健康状态
        
        Returns:
            bool: 服务是否可用
        """
        # 默认实现：尝试生成一个简短的测试音频
        try:
            test_audio = self.text_to_speech("测试")
            return len(test_audio) > 0
        except Exception:
            return False
    
    def apply_emotion_parameters(self, emotion: str, emotion_params: Dict[str, Any]) -> None:
        """应用情感参数到服务配置
        
        Args:
            emotion: 情感类型
            emotion_params: 情感参数字典
        """
        # 子类可以重写此方法来实现特定的参数应用逻辑
        if 'voice_settings' in self.config:
            self.config['voice_settings'].update(emotion_params)
    
    def text_to_speech_with_cache(self, text: str, emotion: Optional[str] = None) -> AudioSegment:
        """带缓存的文本转语音
        
        Args:
            text: 要转换的文本
            emotion: 可选的情感参数
            
        Returns:
            AudioSegment: 音频片段
        """
        # 获取缓存管理器
        cache = get_cache()
        
        # 尝试从缓存获取
        if cache:
            cached_audio = cache.get(text, self.service_name, emotion)
            if cached_audio:
                return cached_audio
        
        # 缓存未命中，生成音频
        audio = self.text_to_speech(text, emotion)
        
        # 存入缓存
        if cache and audio:
            cache.put(text, audio, self.service_name, emotion)
        
        return audio