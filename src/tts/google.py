"""Google TTS服务实现"""
import time
import logging
from pathlib import Path
from typing import Optional
from google.cloud import texttospeech
from google.api_core import exceptions as google_exceptions
from pydub import AudioSegment
import tempfile
import os

from .base import TTSService

logger = logging.getLogger(__name__)


class GoogleTTSService(TTSService):
    """Google TTS服务实现"""
    
    def __init__(self, config: dict):
        """初始化Google TTS服务
        
        Args:
            config: 包含API密钥路径等配置
        """
        super().__init__(config)
        self._init_client()
        
    def validate_config(self) -> None:
        """验证Google TTS配置"""
        if not self.config.get('api_key_path'):
            raise ValueError("Missing 'api_key_path' in Google TTS config")
        
        api_key_path = Path(self.config['api_key_path'])
        if not api_key_path.exists():
            raise FileNotFoundError(f"API key file not found: {api_key_path}")
    
    def _init_client(self) -> None:
        """初始化Google TTS客户端"""
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.config['api_key_path']
        self.client = texttospeech.TextToSpeechClient()
        
        # 配置语音参数
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=self.config.get('language_code', 'zh-CN'),
            name=self.config.get('voice_name', 'zh-CN-Standard-A')
        )
        
        # 配置音频参数
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=self.config.get('speaking_rate', 1.0),
            pitch=self.config.get('pitch', 0.0)
        )
    
    def text_to_speech(self, text: str) -> AudioSegment:
        """将文本转换为语音（带重试机制）
        
        Args:
            text: 要转换的文本
            
        Returns:
            AudioSegment: 音频片段
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 构建请求
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # 调用API
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=self.voice,
                    audio_config=self.audio_config
                )
                
                # 保存到临时文件并加载为AudioSegment
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_file.write(response.audio_content)
                    tmp_path = tmp_file.name
                
                audio = AudioSegment.from_mp3(tmp_path)
                os.unlink(tmp_path)  # 删除临时文件
                
                return audio
                
            except google_exceptions.GoogleAPIError as e:
                logger.error(f"Google TTS API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    raise RuntimeError(f"Failed after {max_retries} attempts: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error in text_to_speech: {e}")
                raise