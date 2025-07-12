"""TTS服务模块"""
from .base import TTSService
from .gptsovits import GPTSoVITSService
from .gemini import GeminiTTSService

# 服务注册表
TTS_SERVICES = {
    'gpt_sovits': GPTSoVITSService,
    'gemini': GeminiTTSService,
}

__all__ = ['TTSService', 'GPTSoVITSService', 'GeminiTTSService', 'TTS_SERVICES']