"""TTS服务模块"""
from .base import TTSService
from .gptsovits import GPTSoVITSService

# 服务注册表
TTS_SERVICES = {
    'gpt_sovits': GPTSoVITSService,
}

__all__ = ['TTSService', 'GPTSoVITSService', 'TTS_SERVICES']