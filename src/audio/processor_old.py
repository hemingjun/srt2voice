"""音频处理器"""
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import timedelta
from pydub import AudioSegment
from pydub.silence import split_on_silence
from dataclasses import dataclass
import numpy as np
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    logger = logging.getLogger(__name__)
    logger.warning("librosa not installed, falling back to basic speed adjustment")

from ..parser.srt import SRTParser

logger = logging.getLogger(__name__)


@dataclass
class OverlapStatistics:
    """音频重叠统计信息"""
    total_overlaps: int = 0
    speed_adjusted: int = 0
    truncated: int = 0
    warned_only: int = 0
    max_speed_factor: float = 1.0
    total_time_adjusted: float = 0.0


class AudioProcessor:
    """音频处理器，负责音频片段的管理和拼接"""
    
    def __init__(self, output_format: str = 'wav', config: Optional[Dict] = None):
        """初始化音频处理器
        
        Args:
            output_format: 输出音频格式，默认为wav
            config: 音频处理配置，包含overlap_handling等设置
        """
        self.output_format = output_format
        self.audio_segments: List[Tuple[float, AudioSegment]] = []
        self.overlap_stats = OverlapStatistics()
        
        # 从配置中获取音频处理设置
        self.config = config or {}
        self.overlap_handling = self.config.get('overlap_handling', 'speed_adjust')
        self.speed_adjust_limit = self.config.get('speed_adjust_limit', 1.5)
        self.fade_duration = self.config.get('fade_duration', 0.0)  # 默认关闭淡出效果
    
    def add_audio_segment(self, start_time: float, audio: AudioSegment, 
                         end_time: Optional[float] = None, 
                         next_start_time: Optional[float] = None) -> None:
        """添加音频片段，可选进行重叠检测和处理
        
        Args:
            start_time: 开始时间（秒）
            audio: 音频片段
            end_time: 字幕结束时间（秒），用于重叠检测
            next_start_time: 下一个字幕开始时间（秒），用于重叠检测
        """
        # 如果提供了时间信息，进行重叠检测
        if end_time is not None:
            audio_duration = len(audio) / 1000.0
            available_duration = end_time - start_time
            
            if next_start_time is not None:
                max_duration = next_start_time - start_time
                available_duration = min(available_duration, max_duration)
            
            # 处理重叠
            if audio_duration > available_duration:
                audio = self._handle_overlap(audio, audio_duration, available_duration)
        
        self.audio_segments.append((start_time, audio))
        logger.debug(f"Added audio segment at {start_time}s")
    
    def process_subtitles(self, subtitles: List[dict], tts_service) -> AudioSegment:
        """处理字幕并生成完整音频，包含重叠检测和处理
        
        Args:
            subtitles: 字幕列表
            tts_service: TTS服务实例
            
        Returns:
            AudioSegment: 完整的音频
        """
        # 清空之前的片段和统计
        self.audio_segments = []
        self.overlap_stats = OverlapStatistics()
        
        # 转换每个字幕为音频
        for i, subtitle in enumerate(subtitles):
            start_time = self._timedelta_to_seconds(subtitle['start'])
            end_time = self._timedelta_to_seconds(subtitle['end'])
            text = subtitle['content']
            
            # 生成音频（第一个片段作为参考）
            if hasattr(tts_service, '_first_segment_path'):
                # GPT-SoVITS 服务，第一个片段需要保存为参考
                audio = tts_service.text_to_speech(text, save_as_reference=(i == 0))
            else:
                # 其他 TTS 服务
                audio = tts_service.text_to_speech(text)
            audio_duration = len(audio) / 1000.0  # 转换为秒
            
            # 计算可用时间窗口
            available_duration = end_time - start_time
            
            # 检查是否会与下一个字幕重叠
            if i < len(subtitles) - 1:
                next_start = self._timedelta_to_seconds(subtitles[i + 1]['start'])
                max_duration = next_start - start_time
                available_duration = min(available_duration, max_duration)
            
            # 处理音频重叠
            if audio_duration > available_duration:
                self.overlap_stats.total_overlaps += 1
                overlap_duration = audio_duration - available_duration
                
                logger.warning(
                    f"Audio overlap detected at subtitle {subtitle.get('index', i+1)}: "
                    f"audio={audio_duration:.2f}s, available={available_duration:.2f}s, "
                    f"overlap={overlap_duration:.2f}s"
                )
                
                if self.overlap_handling == 'speed_adjust':
                    # 计算需要的速度因子
                    speed_factor = audio_duration / available_duration
                    
                    if speed_factor <= self.speed_adjust_limit:
                        # 调整速度
                        audio = self._adjust_audio_speed(audio, speed_factor)
                        self.overlap_stats.speed_adjusted += 1
                        self.overlap_stats.max_speed_factor = max(
                            self.overlap_stats.max_speed_factor, speed_factor
                        )
                        self.overlap_stats.total_time_adjusted += overlap_duration
                        logger.info(f"Applied speed adjustment: {speed_factor:.2f}x")
                    else:
                        # 速度调整超出限制，改为截断
                        audio = self._truncate_with_fade(
                            audio, int(available_duration * 1000)
                        )
                        self.overlap_stats.truncated += 1
                        logger.warning(
                            f"Speed factor {speed_factor:.2f}x exceeds limit, truncating audio"
                        )
                
                elif self.overlap_handling == 'truncate':
                    # 直接截断
                    audio = self._truncate_with_fade(
                        audio, int(available_duration * 1000)
                    )
                    self.overlap_stats.truncated += 1
                
                else:  # 'warn_only'
                    # 仅警告，不做处理
                    self.overlap_stats.warned_only += 1
            
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
    
    def _adjust_audio_speed(self, audio: AudioSegment, speed_factor: float) -> AudioSegment:
        """调整音频速度
        
        Args:
            audio: 原始音频
            speed_factor: 速度因子（>1加速，<1减速）
            
        Returns:
            AudioSegment: 调速后的音频
        """
        if speed_factor == 1.0:
            return audio
        
        if HAS_LIBROSA:
            # 使用 librosa 进行高质量时间拉伸
            try:
                # 将 AudioSegment 转换为 numpy 数组
                samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
                # 归一化到 [-1, 1]
                if audio.sample_width == 2:  # 16-bit
                    samples = samples / 32768.0
                elif audio.sample_width == 4:  # 32-bit
                    samples = samples / 2147483648.0
                
                # 使用 librosa 的时间拉伸，保持音调不变
                stretched = librosa.effects.time_stretch(samples, rate=speed_factor)
                
                # 转换回整数采样
                if audio.sample_width == 2:
                    stretched = (stretched * 32767).astype(np.int16)
                elif audio.sample_width == 4:
                    stretched = (stretched * 2147483647).astype(np.int32)
                
                # 创建新的 AudioSegment
                return AudioSegment(
                    stretched.tobytes(),
                    frame_rate=audio.frame_rate,
                    sample_width=audio.sample_width,
                    channels=audio.channels
                )
            except Exception as e:
                logger.warning(f"Librosa time stretch failed: {e}, falling back to basic method")
        
        # 备用方法：使用pydub的速度调整
        sound_with_altered_frame_rate = audio._spawn(
            audio.raw_data, 
            overrides={
                "frame_rate": int(audio.frame_rate * speed_factor)
            }
        )
        return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
    
    def _truncate_with_fade(self, audio: AudioSegment, max_duration_ms: int) -> AudioSegment:
        """截断音频并添加淡出效果
        
        Args:
            audio: 原始音频
            max_duration_ms: 最大时长（毫秒）
            
        Returns:
            AudioSegment: 截断后的音频
        """
        if len(audio) <= max_duration_ms:
            return audio
        
        # 截断到最大时长
        truncated = audio[:max_duration_ms]
        
        # 添加淡出效果
        fade_duration_ms = int(self.fade_duration * 1000)
        if fade_duration_ms > 0 and len(truncated) > fade_duration_ms:
            truncated = truncated.fade_out(fade_duration_ms)
        
        return truncated
    
    def _handle_overlap(self, audio: AudioSegment, audio_duration: float, 
                       available_duration: float) -> AudioSegment:
        """处理音频重叠
        
        Args:
            audio: 原始音频
            audio_duration: 音频时长（秒）
            available_duration: 可用时长（秒）
            
        Returns:
            AudioSegment: 处理后的音频
        """
        self.overlap_stats.total_overlaps += 1
        overlap_duration = audio_duration - available_duration
        
        logger.warning(
            f"Audio overlap detected: audio={audio_duration:.2f}s, "
            f"available={available_duration:.2f}s, overlap={overlap_duration:.2f}s"
        )
        
        if self.overlap_handling == 'speed_adjust':
            speed_factor = audio_duration / available_duration
            
            if speed_factor <= self.speed_adjust_limit:
                audio = self._adjust_audio_speed(audio, speed_factor)
                self.overlap_stats.speed_adjusted += 1
                self.overlap_stats.max_speed_factor = max(
                    self.overlap_stats.max_speed_factor, speed_factor
                )
                self.overlap_stats.total_time_adjusted += overlap_duration
                logger.info(f"Applied speed adjustment: {speed_factor:.2f}x")
            else:
                audio = self._truncate_with_fade(
                    audio, int(available_duration * 1000)
                )
                self.overlap_stats.truncated += 1
                logger.warning(
                    f"Speed factor {speed_factor:.2f}x exceeds limit, truncating audio"
                )
        
        elif self.overlap_handling == 'truncate':
            audio = self._truncate_with_fade(
                audio, int(available_duration * 1000)
            )
            self.overlap_stats.truncated += 1
        
        else:  # 'warn_only'
            self.overlap_stats.warned_only += 1
        
        return audio
    
    def get_overlap_statistics(self) -> Dict[str, any]:
        """获取音频重叠处理统计信息
        
        Returns:
            Dict: 统计信息字典
        """
        return {
            'total_overlaps': self.overlap_stats.total_overlaps,
            'speed_adjusted': self.overlap_stats.speed_adjusted,
            'truncated': self.overlap_stats.truncated,
            'warned_only': self.overlap_stats.warned_only,
            'max_speed_factor': round(self.overlap_stats.max_speed_factor, 2),
            'total_time_adjusted': round(self.overlap_stats.total_time_adjusted, 2)
        }