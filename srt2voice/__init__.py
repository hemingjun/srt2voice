"""
SRT2Voice - 智能字幕转语音工具

将SRT字幕文件转换为自然流畅的语音，支持中英文混合。
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .parser import SRTParser
from .tts import TTSGenerator
from .audio import AudioProcessor
from .config import ConfigManager

__all__ = ["SRTParser", "TTSGenerator", "AudioProcessor", "ConfigManager"]