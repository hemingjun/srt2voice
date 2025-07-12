"""TTS服务模块"""
from .base import TTSService
from .google import GoogleTTSService
from .gptsovits import GPTSoVITSService

# 服务注册表
TTS_SERVICES = {
    'google': GoogleTTSService,
    'gpt_sovits': GPTSoVITSService,
}

__all__ = ['TTSService', 'GoogleTTSService', 'GPTSoVITSService', 'TTS_SERVICES']