"""
音频处理模块
负责音频片段的合成和时间对齐
"""

from pydub import AudioSegment
import io
from typing import List, Dict, Optional
from pathlib import Path


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        """初始化音频处理器"""
        self.segments = []
        
    def add_segment(self, audio_data: bytes, start_time: float, end_time: float, text: str = ""):
        """
        添加音频片段
        
        Args:
            audio_data: 音频二进制数据
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            text: 对应的文本（可选，用于调试）
        """
        # 从内存加载音频
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        
        self.segments.append({
            'audio': audio,
            'start': start_time,
            'end': end_time,
            'duration': len(audio) / 1000.0,  # 实际音频时长（秒）
            'text': text
        })
    
    def align_and_merge(self, allow_overlap: bool = False) -> AudioSegment:
        """
        对齐并合并音频片段
        
        Args:
            allow_overlap: 是否允许音频重叠
            
        Returns:
            合并后的完整音频
        """
        if not self.segments:
            raise ValueError("没有可合并的音频片段")
        
        # 按开始时间排序
        self.segments.sort(key=lambda x: x['start'])
        
        # 创建最终音频
        final_audio = AudioSegment.empty()
        current_time = 0
        
        for i, segment in enumerate(self.segments):
            # 计算理想的开始时间
            ideal_start = segment['start']
            
            # 计算需要的静音时长
            gap = ideal_start - current_time
            
            if gap > 0:
                # 添加静音填充
                silence = AudioSegment.silent(duration=int(gap * 1000))
                final_audio += silence
                current_time += gap
            elif gap < 0 and not allow_overlap:
                # 音频可能重叠，调整开始时间
                # 这种情况下，我们直接连接音频，允许一定的时间偏差
                pass
            
            # 添加音频片段
            final_audio += segment['audio']
            current_time = ideal_start + segment['duration']
            
            # 调试信息
            if segment.get('text'):
                actual_duration = segment['duration']
                expected_duration = segment['end'] - segment['start']
                if abs(actual_duration - expected_duration) > expected_duration * 0.15:
                    print(f"警告: 第{i+1}段音频时长偏差较大")
                    print(f"  文本: {segment['text'][:30]}...")
                    print(f"  预期时长: {expected_duration:.2f}秒")
                    print(f"  实际时长: {actual_duration:.2f}秒")
        
        return final_audio
    
    def export(self, output_path: str, format: str = "mp3", bitrate: str = "128k", parameters: Optional[Dict] = None):
        """
        导出音频文件
        
        Args:
            output_path: 输出文件路径
            format: 音频格式 (mp3, wav等)
            bitrate: 比特率
            parameters: 其他导出参数
        """
        # 合并音频
        audio = self.align_and_merge()
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 导出参数
        export_params = {
            "format": format,
            "bitrate": bitrate
        }
        
        if parameters:
            export_params.update(parameters)
        
        # 导出文件
        audio.export(output_path, **export_params)
    
    def get_total_duration(self) -> float:
        """获取合并后的总时长（秒）"""
        if not self.segments:
            return 0.0
        
        # 最后一个片段的结束时间
        last_segment = max(self.segments, key=lambda x: x['start'])
        return last_segment['start'] + last_segment['duration']
    
    def clear(self):
        """清空所有音频片段"""
        self.segments = []