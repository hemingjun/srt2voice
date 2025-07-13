"""音频时长检测和调整模块"""
import logging
from typing import Tuple, Optional
from pydub import AudioSegment
from datetime import timedelta

logger = logging.getLogger(__name__)


class AudioTimingManager:
    """音频时长管理器，处理音频重叠和时长调整"""
    
    def __init__(self, overlap_handling: str = 'speed_adjust', 
                 speed_adjust_limit: float = 1.5,
                 fade_duration: float = 0.05):
        """初始化时长管理器
        
        Args:
            overlap_handling: 重叠处理策略 ('speed_adjust', 'truncate', 'warn_only')
            speed_adjust_limit: 最大调速倍数
            fade_duration: 淡入淡出时长（秒）
        """
        self.overlap_handling = overlap_handling
        self.speed_adjust_limit = speed_adjust_limit
        self.fade_duration_ms = int(fade_duration * 1000)
        self.stats = {
            'overlaps_detected': 0,
            'speed_adjustments': [],
            'truncations': 0
        }
    
    def check_and_adjust_audio(self, 
                              audio: AudioSegment,
                              start_time: float,
                              end_time: float,
                              subtitle_index: int,
                              subtitle_text: str) -> Tuple[AudioSegment, Optional[str]]:
        """检查并调整音频以适应时间窗口
        
        Args:
            audio: 原始音频片段
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            subtitle_index: 字幕索引（用于日志）
            subtitle_text: 字幕文本（用于日志）
            
        Returns:
            Tuple[AudioSegment, Optional[str]]: 调整后的音频和警告信息
        """
        # 计算可用时长和实际时长
        available_duration = end_time - start_time
        actual_duration = len(audio) / 1000.0  # 转换为秒
        
        # 如果音频时长没有超过可用时间，直接返回
        if actual_duration <= available_duration:
            return audio, None
        
        # 检测到重叠
        self.stats['overlaps_detected'] += 1
        overlap_duration = actual_duration - available_duration
        overlap_percentage = (overlap_duration / actual_duration) * 100
        
        warning_msg = (
            f"字幕 #{subtitle_index}: 音频时长({actual_duration:.2f}s)超过可用时间"
            f"({available_duration:.2f}s)，重叠{overlap_duration:.2f}s "
            f"({overlap_percentage:.1f}%)"
        )
        
        # 根据策略处理
        if self.overlap_handling == 'warn_only':
            # 仅警告，不做调整
            logger.warning(f"{warning_msg} - 保持原样")
            return audio, warning_msg
        
        elif self.overlap_handling == 'speed_adjust':
            # 计算需要的加速倍数
            required_speed = actual_duration / available_duration
            
            if required_speed <= self.speed_adjust_limit:
                # 在限制范围内，进行调速
                adjusted_audio = self._adjust_speed(audio, required_speed)
                self.stats['speed_adjustments'].append(required_speed)
                
                adjust_msg = f"{warning_msg} - 已调速至{required_speed:.2f}x"
                logger.info(adjust_msg)
                return adjusted_audio, adjust_msg
            else:
                # 超过限制，使用最大调速并警告
                adjusted_audio = self._adjust_speed(audio, self.speed_adjust_limit)
                self.stats['speed_adjustments'].append(self.speed_adjust_limit)
                
                remaining_overlap = actual_duration / self.speed_adjust_limit - available_duration
                adjust_msg = (
                    f"{warning_msg} - 已调速至最大值{self.speed_adjust_limit}x，"
                    f"仍有{remaining_overlap:.2f}s重叠"
                )
                logger.warning(adjust_msg)
                return adjusted_audio, adjust_msg
        
        elif self.overlap_handling == 'truncate':
            # 截断音频
            truncated_audio = self._truncate_audio(audio, available_duration)
            self.stats['truncations'] += 1
            
            truncate_msg = f"{warning_msg} - 已截断音频"
            logger.info(truncate_msg)
            return truncated_audio, truncate_msg
        
        else:
            # 未知策略，返回原音频
            logger.error(f"未知的重叠处理策略: {self.overlap_handling}")
            return audio, warning_msg
    
    def _adjust_speed(self, audio: AudioSegment, speed_factor: float) -> AudioSegment:
        """调整音频播放速度
        
        Args:
            audio: 原始音频
            speed_factor: 速度因子（>1表示加速）
            
        Returns:
            AudioSegment: 调速后的音频
        """
        # 使用pydub的speedup方法，保持音调
        # 注意：speedup只能加速，不能减速
        if speed_factor > 1:
            # 计算新的采样率来实现加速
            new_sample_rate = int(audio.frame_rate * speed_factor)
            # 改变采样率但保持帧数，实现加速效果
            speed_audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": new_sample_rate
            })
            # 重新采样回原始采样率
            return speed_audio.set_frame_rate(audio.frame_rate)
        else:
            # 如果需要减速（speed_factor < 1），暂不支持
            return audio
    
    def _truncate_audio(self, audio: AudioSegment, max_duration: float) -> AudioSegment:
        """截断音频到指定时长，并添加淡出效果
        
        Args:
            audio: 原始音频
            max_duration: 最大时长（秒）
            
        Returns:
            AudioSegment: 截断后的音频
        """
        max_duration_ms = int(max_duration * 1000)
        
        # 如果音频已经短于最大时长，直接返回
        if len(audio) <= max_duration_ms:
            return audio
        
        # 截断到最大时长
        truncated = audio[:max_duration_ms]
        
        # 添加淡出效果（如果有足够的时长）
        if len(truncated) > self.fade_duration_ms:
            truncated = truncated.fade_out(self.fade_duration_ms)
        
        return truncated
    
    def get_stats_summary(self) -> dict:
        """获取统计摘要
        
        Returns:
            dict: 统计信息
        """
        summary = {
            'overlaps_detected': self.stats['overlaps_detected'],
            'truncations': self.stats['truncations']
        }
        
        if self.stats['speed_adjustments']:
            adjustments = self.stats['speed_adjustments']
            summary['speed_adjustments_count'] = len(adjustments)
            summary['avg_speed_adjustment'] = sum(adjustments) / len(adjustments)
            summary['max_speed_adjustment'] = max(adjustments)
            summary['min_speed_adjustment'] = min(adjustments)
        
        return summary
    
    def format_adjustment_percentage(self, speed: float) -> str:
        """格式化速度调整为百分比
        
        Args:
            speed: 速度倍数
            
        Returns:
            str: 格式化的百分比字符串
        """
        percentage = (speed - 1) * 100
        if percentage > 0:
            return f"+{percentage:.1f}%"
        else:
            return f"{percentage:.1f}%"