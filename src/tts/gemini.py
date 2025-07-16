"""Google Gemini TTS服务实现"""
import io
import os
import wave
import base64
import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from pydub import AudioSegment
from .base import TTSService

logger = logging.getLogger(__name__)


class GeminiTTSService(TTSService):
    """Google Gemini TTS服务
    
    使用Gemini 2.5 Pro Preview TTS模型
    支持24种语言的高质量语音合成
    """
    
    def __init__(self, config: dict):
        """初始化Gemini TTS服务
        
        Args:
            config: 服务配置字典
        """
        # 先设置必要的属性，再调用父类构造函数
        self.api_key = config['credentials'].get('api_key') or os.getenv('GEMINI_API_KEY')
        self.model_name = config['voice_settings'].get('model', 'gemini-2.5-pro-preview-tts')
        self.voice_name = config['voice_settings'].get('voice_name', 'Kore')
        
        # 初始化客户端
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"初始化Gemini TTS服务，模型：{self.model_name}，声音：{self.voice_name}")
            except Exception as e:
                logger.error(f"初始化Gemini客户端失败：{e}")
        
        # 调用父类构造函数，会触发validate_config
        super().__init__(config)
    
    def validate_config(self) -> None:
        """验证配置有效性"""
        if not self.api_key:
            raise ValueError(
                "缺少Gemini API密钥：请设置 credentials.api_key 或 GEMINI_API_KEY 环境变量"
            )
        
        if not self.client:
            raise ValueError("无法初始化Gemini客户端")
        
        # 验证模型名称
        valid_models = ['gemini-2.5-flash-preview-tts', 'gemini-2.5-pro-preview-tts']
        if self.model_name not in valid_models:
            logger.warning(
                f"模型 {self.model_name} 可能不支持TTS，推荐使用：{valid_models}"
            )
    
    def text_to_speech(self, text: str) -> AudioSegment:
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            
        Returns:
            AudioSegment: 音频片段
        """
        
        try:
            # 添加调试日志确保使用一致的声音
            logger.debug(f"使用声音: {self.voice_name}")
            
            # 构建生成配置
            config = types.GenerateContentConfig(
                # 设置响应类型为音频
                response_modalities=["AUDIO"],
                # 配置语音参数
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                )
            )
            
            # 调用模型生成音频
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=config
            )
            
            # 检查响应
            if not response or not response.candidates:
                raise Exception("API未返回响应")
            
            # 从响应中提取音频数据
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise Exception("响应中没有内容")
            
            # 获取音频数据
            audio_data = candidate.content.parts[0].inline_data.data
            
            # 智能检测数据格式
            if isinstance(audio_data, str):
                # 如果是字符串，尝试base64解码
                try:
                    audio_data = base64.b64decode(audio_data)
                    logger.debug("音频数据已从base64字符串解码")
                except Exception as e:
                    logger.warning(f"Base64解码失败，尝试转换为bytes: {e}")
                    audio_data = audio_data.encode()
            elif isinstance(audio_data, bytes):
                # 检测是否可能是base64编码的bytes
                try:
                    # 尝试解码，如果成功且是有效音频数据则使用
                    decoded = base64.b64decode(audio_data, validate=True)
                    # 简单检查：PCM数据应该有一定长度
                    if len(decoded) > 1000:
                        audio_data = decoded
                        logger.debug("音频数据已从base64 bytes解码")
                except Exception:
                    # 不是base64，保持原样
                    logger.debug("音频数据是原始二进制格式")
            
            # 添加调试日志
            logger.debug(f"音频数据类型: {type(audio_data)}, 长度: {len(audio_data) if audio_data else 0}")
            
            # Gemini返回的是原始PCM数据，需要构建WAV格式
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位（2字节）
                wav_file.setframerate(24000)  # 24kHz
                wav_file.writeframes(audio_data)
            
            # 回到开始位置
            wav_buffer.seek(0)
            
            # 转换为AudioSegment
            audio = AudioSegment.from_wav(wav_buffer)
            
            # 转换为项目标准格式（32kHz）
            if audio.frame_rate != 32000:
                audio = audio.set_frame_rate(32000)
            
            logger.info(f"文本转语音成功，时长：{len(audio)/1000:.2f}秒")
            return audio
            
        except Exception as e:
            logger.error(f"Gemini TTS调用失败：{str(e)}")
            raise
    
    def check_health(self) -> bool:
        """检查服务健康状态
        
        Returns:
            bool: 服务是否可用
        """
        if not self.client:
            return False
            
        try:
            # 生成一个简短的测试音频
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                )
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="测试",
                config=config
            )
            
            return bool(response)
            
        except Exception as e:
            logger.warning(f"Gemini服务健康检查失败：{str(e)}")
            return False
    
