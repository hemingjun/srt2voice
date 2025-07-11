"""
SRT文件解析模块
负责读取和解析SRT字幕文件
"""

from pathlib import Path
from typing import List, Dict
import pysrt


class SRTParser:
    """SRT文件解析器"""
    
    def __init__(self, file_path: str):
        """
        初始化解析器
        
        Args:
            file_path: SRT文件路径
        """
        self.file_path = Path(file_path)
        self.subtitles = []
        
    def parse(self) -> List[Dict]:
        """
        解析SRT文件
        
        Returns:
            字幕列表，每个字幕包含：
            - index: 序号
            - start: 开始时间（秒）
            - end: 结束时间（秒）
            - text: 文本内容
            - duration: 持续时间（秒）
        """
        try:
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'gb18030']:
                try:
                    subs = pysrt.open(self.file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("无法解析文件编码")
            
            # 转换为标准格式
            for sub in subs:
                self.subtitles.append({
                    'index': sub.index,
                    'start': sub.start.ordinal / 1000.0,  # 转换为秒
                    'end': sub.end.ordinal / 1000.0,
                    'text': sub.text.strip(),
                    'duration': (sub.end - sub.start).ordinal / 1000.0
                })
            
            return self.subtitles
            
        except Exception as e:
            raise ValueError(f"SRT文件解析失败: {e}")
    
    def validate(self) -> bool:
        """验证SRT文件格式是否正确"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        
        if not self.file_path.suffix.lower() == '.srt':
            raise ValueError(f"不是SRT文件: {self.file_path}")
        
        return True
    
    def get_total_duration(self) -> float:
        """获取字幕总时长（秒）"""
        if not self.subtitles:
            self.parse()
        
        if self.subtitles:
            return self.subtitles[-1]['end']
        return 0.0
    
    def get_character_count(self) -> int:
        """获取总字符数（用于费用估算）"""
        if not self.subtitles:
            self.parse()
        
        return sum(len(sub['text']) for sub in self.subtitles)