"""情感控制模块"""
from .controller import EmotionController, EmotionSequence
from .presets import get_all_emotions, get_service_emotions

__all__ = ['EmotionController', 'EmotionSequence', 'get_all_emotions', 'get_service_emotions']