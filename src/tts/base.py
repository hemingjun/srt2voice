"""TTS服务抽象基类"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from pydub import AudioSegment


class TTSService(ABC):
    """TTS服务抽象基类"""
    
    def __init__(self, config: dict):
        """初始化TTS服务
        
        Args:
            config: 服务配置字典
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> None:
        """验证配置有效性"""
        pass
    
    @abstractmethod
    def text_to_speech(self, text: str) -> AudioSegment:
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            
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