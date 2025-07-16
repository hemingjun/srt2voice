"""音频时长估算模块"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TimingController:
    """时长估算器，负责文本时长预估算和标点优化"""
    
    # 不同字符类型的预估时长（秒/字符）
    # 基于GPT-SoVITS实际测试优化
    # 测试数据：使用reference_8s.wav，7个中文字符约1.78秒 = 0.254秒/字
    CHAR_DURATIONS = {
        'chinese': 0.25,      # 中文字符（基于实测调整）
        'english': 0.08,      # 英文字符（按字母算）
        'number': 0.20,       # 数字
        'punctuation': 0.10,  # 标点符号
        'space': 0.05,        # 空格
        'default': 0.20       # 默认值
    }
    
    # 标点优化级别（按停顿时长排序）
    # 级别1：删除长停顿标点（影响最大）
    LEVEL1_REMOVE = ['——', '—', '……', '…', '～～', '～']
    
    # 级别2：删除中等停顿标点
    LEVEL2_REMOVE = LEVEL1_REMOVE + ['、', '；', ';', '：', ':', '·']
    
    # 级别3：删除短停顿标点（保留句末标点）
    LEVEL3_REMOVE = LEVEL2_REMOVE + ['，', ',']
    
    def __init__(self, config: Optional[dict] = None):
        """初始化时长估算器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
    
    def estimate_duration(self, text: str) -> float:
        """精确估算文本的语音时长
        
        Args:
            text: 输入文本
            
        Returns:
            float: 预估时长（秒）
        """
        total_duration = 0.0
        
        for char in text:
            char_type = self._get_char_type(char)
            duration = self.CHAR_DURATIONS.get(char_type, self.CHAR_DURATIONS['default'])
            total_duration += duration
        
        # 考虑语速变化因素
        # 长句子通常读得稍快
        if len(text) > 50:
            total_duration *= 0.95
        elif len(text) > 30:
            total_duration *= 0.98
        
        # 包含数字或英文的混合文本通常更慢
        if self._has_mixed_content(text):
            total_duration *= 1.1
        
        # 添加基础停顿时间（较短）
        total_duration += 0.1
        
        return total_duration
    
    def _get_char_type(self, char: str) -> str:
        """判断字符类型
        
        Args:
            char: 单个字符
            
        Returns:
            str: 字符类型
        """
        if '\u4e00' <= char <= '\u9fff':
            return 'chinese'
        elif char.isalpha():
            return 'english'
        elif char.isdigit():
            return 'number'
        elif char.isspace():
            return 'space'
        elif not char.isalnum():
            return 'punctuation'
        else:
            return 'default'
    
    def _has_mixed_content(self, text: str) -> bool:
        """检查是否包含混合内容（中英文混合、包含数字等）
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否为混合内容
        """
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        has_english = bool(re.search(r'[a-zA-Z]', text))
        has_number = bool(re.search(r'\d', text))
        
        # 至少包含两种类型
        return sum([has_chinese, has_english, has_number]) >= 2
    
    def optimize_punctuation(self, text: str, level: int) -> str:
        """根据优化级别删减标点符号
        
        Args:
            text: 输入文本
            level: 优化级别 (1-3)
                1: 删除破折号、省略号等长停顿标点
                2: 删除顿号、分号、冒号等中等停顿标点
                3: 删除逗号等短停顿标点
                
        Returns:
            str: 优化后的文本
        """
        if level < 1 or level > 3:
            return text
            
        # 根据级别选择要删除的标点
        if level == 1:
            punctuations_to_remove = self.LEVEL1_REMOVE
        elif level == 2:
            punctuations_to_remove = self.LEVEL2_REMOVE
        else:  # level == 3
            punctuations_to_remove = self.LEVEL3_REMOVE
        
        # 删除指定的标点符号
        optimized_text = text
        for punct in punctuations_to_remove:
            optimized_text = optimized_text.replace(punct, '')
        
        # 记录优化信息
        if optimized_text != text:
            logger.info(
                f"标点优化级别{level}: "
                f"原文长度={len(text)}, 优化后长度={len(optimized_text)}, "
                f"删除字符数={len(text) - len(optimized_text)}"
            )
            logger.debug(f"原文: {text}")
            logger.debug(f"优化: {optimized_text}")
        
        return optimized_text