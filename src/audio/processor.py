"""音频处理器"""
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import timedelta
from pydub import AudioSegment
from pydub.silence import split_on_silence

from ..parser.srt import SRTParser

logger = logging.getLogger(__name__)


class AudioProcessor:
    """音频处理器，负责音频片段的管理和拼接"""
    
    def __init__(self, output_format: str = 'wav'):
        """初始化音频处理器
        
        Args:
            output_format: 输出音频格式，默认为wav
        """
        self.output_format = output_format
        self.audio_segments: List[Tuple[float, AudioSegment]] = []
    
    def add_audio_segment(self, start_time: float, audio: AudioSegment) -> None:
        """添加音频片段
        
        Args:
            start_time: 开始时间（秒）
            audio: 音频片段
        """
        self.audio_segments.append((start_time, audio))
        logger.debug(f"Added audio segment at {start_time}s")
    
    def process_subtitles(self, subtitles: List[dict], tts_service) -> AudioSegment:
        """处理字幕并生成完整音频
        
        Args:
            subtitles: 字幕列表
            tts_service: TTS服务实例
            
        Returns:
            AudioSegment: 完整的音频
        """
        # 清空之前的片段
        self.audio_segments = []
        
        # 转换每个字幕为音频
        for subtitle in subtitles:
            start_time = self._timedelta_to_seconds(subtitle['start'])
            text = subtitle['content']
            
            # 生成音频
            audio = tts_service.text_to_speech(text)
            self.add_audio_segment(start_time, audio)
        
        # 拼接音频
        return self._concatenate_audio()
    
    def _timedelta_to_seconds(self, td: timedelta) -> float:
        """将timedelta转换为秒数
        
        Args:
            td: timedelta对象
            
        Returns:
            float: 秒数
        """
        return td.total_seconds()
    
    def _concatenate_audio(self) -> AudioSegment:
        """拼接音频片段
        
        Returns:
            AudioSegment: 拼接后的完整音频
        """
        if not self.audio_segments:
            return AudioSegment.empty()
        
        # 按开始时间排序
        self.audio_segments.sort(key=lambda x: x[0])
        
        # 获取总时长（最后一个片段的结束时间）
        last_start, last_audio = self.audio_segments[-1]
        total_duration = last_start + len(last_audio) / 1000.0  # 转换为秒
        
        # 创建静音的完整音频
        complete_audio = AudioSegment.silent(duration=int(total_duration * 1000))
        
        # 将每个片段插入到正确的位置
        for start_time, audio in self.audio_segments:
            position_ms = int(start_time * 1000)
            # 叠加音频片段
            complete_audio = complete_audio.overlay(audio, position=position_ms)
        
        return complete_audio
    
    def save_audio(self, audio: AudioSegment, output_path: Path) -> None:
        """保存音频文件
        
        Args:
            audio: 音频片段
            output_path: 输出路径
        """
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 导出音频
        audio.export(output_path, format=self.output_format)
        logger.info(f"Audio saved to: {output_path}")
    
    @staticmethod
    def create_silent_audio(duration_ms: int) -> AudioSegment:
        """创建静音音频
        
        Args:
            duration_ms: 时长（毫秒）
            
        Returns:
            AudioSegment: 静音音频
        """
        return AudioSegment.silent(duration=duration_ms)