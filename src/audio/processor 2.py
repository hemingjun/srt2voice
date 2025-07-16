"""音频处理器 - 简化版本"""
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import timedelta
from pydub import AudioSegment
from dataclasses import dataclass

from ..parser.srt import SRTParser
from .timing import TimingController
from .exceptions import AudioTooLongError

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatistics:
    """音频处理统计信息"""
    total_segments: int = 0
    text_optimized: int = 0  # 进行了文本优化的数量
    over_duration: int = 0  # 轻微超长的数量
    max_optimization_level: int = 0  # 最大优化级别


class AudioProcessor:
    """音频处理器，负责音频片段的管理和拼接"""
    
    def __init__(self, output_format: str = 'wav', config: Optional[Dict] = None):
        """初始化音频处理器
        
        Args:
            output_format: 输出音频格式，默认为wav
            config: 音频处理配置
        """
        self.output_format = output_format
        self.audio_segments: List[Tuple[float, AudioSegment]] = []
        self.processing_stats = ProcessingStatistics()
        
        # 从配置中获取音频处理设置
        self.config = config or {}
        
        # 初始化时长控制器
        timing_config = self.config.get('timing', {})
        self.timing_controller = TimingController(timing_config)
    
    def process_subtitles(self, subtitles: List[dict], tts_service) -> AudioSegment:
        """处理字幕并生成完整音频
        
        Args:
            subtitles: 字幕列表
            tts_service: TTS服务实例
            
        Returns:
            AudioSegment: 完整的音频
        """
        # 清空之前的片段和统计
        self.audio_segments = []
        self.processing_stats = ProcessingStatistics()
        self.processing_stats.total_segments = len(subtitles)
        
        # 计算总时长（基于字幕时间轴）
        if subtitles:
            self.total_duration = self._timedelta_to_seconds(subtitles[-1]['end'])
        else:
            self.total_duration = 0
        
        # 转换每个字幕为音频
        for i, subtitle in enumerate(subtitles):
            self._process_single_subtitle(i, subtitle, tts_service)
        
        # 拼接音频
        return self._concatenate_audio()
    
    def _process_single_subtitle(self, index: int, subtitle: dict, tts_service) -> None:
        """处理单个字幕
        
        Args:
            index: 字幕索引
            subtitle: 当前字幕
            tts_service: TTS服务实例
        """
        start_time = self._timedelta_to_seconds(subtitle['start'])
        end_time = self._timedelta_to_seconds(subtitle['end'])
        text = subtitle['content']
        
        # 计算可用时间窗口 - 使用字幕本身的时长
        available_duration = end_time - start_time
        
        # 使用时长控制器分析文本
        estimated_duration = self.timing_controller.estimate_duration(text)
        logger.info(
            f"字幕 {subtitle.get('index', index+1)}: "
            f"文本='{text[:20]}...', 长度={len(text)}字, "
            f"预估时长={estimated_duration:.2f}s, "
            f"可用时长={available_duration:.2f}s, "
            f"开始={start_time:.2f}s, 结束={end_time:.2f}s"
        )
        
        # 直接处理整个文本，不分句
        audio = self._generate_subtitle_audio(
            text, estimated_duration, available_duration, tts_service, 
            is_first=(index == 0)
        )
        self.add_audio_segment(start_time, audio)
    
    def _generate_subtitle_audio(self, text: str, estimated_duration: float, 
                                target_duration: float, tts_service, 
                                is_first: bool = False) -> AudioSegment:
        """生成字幕音频，包含重试机制
        
        Args:
            text: 字幕文本
            estimated_duration: 预估时长（秒）
            target_duration: 目标时长（秒）
            tts_service: TTS服务实例
            is_first: 是否为第一个字幕
            
        Returns:
            AudioSegment: 生成的音频
        """
        max_retries = 3
        retry_count = 0
        current_text = text
        
        while retry_count < max_retries:
            try:
                # 如果是重试，应用标点优化
                if retry_count > 0:
                    current_text = self.timing_controller.optimize_punctuation(text, retry_count)
                    logger.info(f"第 {retry_count} 次重试，使用标点优化级别 {retry_count}")
                
                logger.info(
                    f"生成音频: 文本长度={len(current_text)}字, "
                    f"预估时长={estimated_duration:.2f}s, "
                    f"目标时长={target_duration:.2f}s, "
                    f"重试次数={retry_count}"
                )
                
                # 生成音频
                if hasattr(tts_service, '_first_segment_path'):
                    # GPT-SoVITS 服务
                    audio = tts_service.text_to_speech(
                        current_text,
                        save_as_reference=is_first and retry_count == 0  # 只在第一次尝试时保存参考
                    )
                else:
                    # 其他 TTS 服务
                    audio = tts_service.text_to_speech(current_text)
                
                # 检查实际时长
                actual_duration = len(audio) / 1000.0
                duration_ratio = actual_duration / target_duration
                
                logger.info(
                    f"生成结果: 实际时长={actual_duration:.2f}s, "
                    f"时长比例={duration_ratio:.2f}x"
                )
                
                # 根据超长程度处理
                if duration_ratio > 1.5:  # 超过1.5倍，需要重新生成
                    if retry_count < max_retries - 1:
                        logger.warning(
                            f"音频超长: {actual_duration:.2f}s > {target_duration:.2f}s ({duration_ratio:.1f}x), 准备重试"
                        )
                        retry_count += 1
                        continue
                    else:
                        # 最后一次重试仍然失败
                        error_msg = (
                            f"音频生成失败：经过 {max_retries} 次尝试，仍无法生成符合时长要求的音频。"
                            f"原始文本: '{text[:30]}...', "
                            f"目标时长: {target_duration:.2f}s, "
                            f"实际时长: {actual_duration:.2f}s"
                        )
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
                
                # 音频时长在合理范围内
                if retry_count > 0:
                    self.processing_stats.text_optimized += 1
                    self.processing_stats.max_optimization_level = max(
                        self.processing_stats.max_optimization_level, retry_count
                    )
                
                if duration_ratio > 1.2:
                    logger.info(
                        f"音频略长但可接受: {actual_duration:.2f}s vs {target_duration:.2f}s ({duration_ratio:.1f}x)"
                    )
                    self.processing_stats.over_duration += 1
                
                return audio
                
            except Exception as e:
                if retry_count < max_retries - 1:
                    logger.warning(f"生成音频时出错: {str(e)}, 准备重试")
                    retry_count += 1
                else:
                    raise
        
        # 音频过长，且已经尝试了所有优化措施
        logger.error(f"音频时长无法优化到目标范围内，已尝试{max_retries}次")
        raise AudioTooLongError(
            f"音频过长无法优化: {actual_duration:.2f}s vs {target_duration:.2f}s",
            actual_duration=actual_duration,
            target_duration=target_duration,
            retry_count=max_retries
        )
    
    def add_audio_segment(self, start_time: float, audio: AudioSegment, 
                         end_time: Optional[float] = None, 
                         next_start_time: Optional[float] = None) -> None:
        """添加音频片段
        
        Args:
            start_time: 开始时间（秒）
            audio: 音频片段
            end_time: 字幕结束时间（秒），用于重叠检测
            next_start_time: 下一个字幕开始时间（秒），用于重叠检测
        """
        self.audio_segments.append((start_time, audio))
        logger.debug(f"Added audio segment at {start_time}s")
    
    def _timedelta_to_seconds(self, td: timedelta) -> float:
        """将timedelta转换为秒数
        
        Args:
            td: timedelta对象
            
        Returns:
            float: 秒数
        """
        return td.total_seconds()
    
    def _concatenate_audio(self) -> AudioSegment:
        """串联音频片段，确保不重叠
        
        Returns:
            AudioSegment: 拼接后的完整音频
        """
        if not self.audio_segments:
            return AudioSegment.empty()
        
        # 按开始时间排序
        self.audio_segments.sort(key=lambda x: x[0])
        
        # 创建空音频作为基础
        complete_audio = AudioSegment.empty()
        last_end_time_ms = 0
        
        for i, (start_time, audio) in enumerate(self.audio_segments):
            start_time_ms = int(start_time * 1000)
            audio_duration_ms = len(audio)
            
            # 计算需要插入的静音长度
            if start_time_ms > last_end_time_ms:
                # 正常情况：添加静音填充
                silence_duration = start_time_ms - last_end_time_ms
                if silence_duration > 0:
                    complete_audio += AudioSegment.silent(duration=silence_duration)
            elif start_time_ms < last_end_time_ms:
                # 重叠情况：记录警告，但仍然串联（避免重叠）
                overlap_ms = last_end_time_ms - start_time_ms
                logger.warning(
                    f"检测到音频重叠: 片段 {i+1} 应在 {start_time_ms}ms 开始，"
                    f"但前一片段在 {last_end_time_ms}ms 结束（重叠 {overlap_ms}ms）"
                )
            
            # 添加音频片段
            complete_audio += audio
            last_end_time_ms = last_end_time_ms + audio_duration_ms if start_time_ms < last_end_time_ms else start_time_ms + audio_duration_ms
            
            logger.debug(
                f"片段 {i+1}: 原始开始时间={start_time:.2f}s, "
                f"实际位置={len(complete_audio) - len(audio)}ms, "
                f"时长={audio_duration_ms}ms"
            )
        
        # 如果最终音频短于原始字幕总时长，添加尾部静音
        if self.total_duration > 0:
            expected_duration_ms = int(self.total_duration * 1000)
            actual_duration_ms = len(complete_audio)
            if actual_duration_ms < expected_duration_ms:
                tail_silence = expected_duration_ms - actual_duration_ms
                complete_audio += AudioSegment.silent(duration=tail_silence)
                logger.debug(f"添加尾部静音: {tail_silence}ms")
        
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
    
    def get_processing_statistics(self) -> Dict[str, any]:
        """获取音频处理统计信息
        
        Returns:
            Dict: 统计信息字典
        """
        return {
            'total_segments': self.processing_stats.total_segments,
            'text_optimized': self.processing_stats.text_optimized,
            'over_duration': self.processing_stats.over_duration,
            'max_optimization_level': self.processing_stats.max_optimization_level
        }