"""
工具函数模块
提供通用的工具函数和装饰器
"""

from datetime import datetime
import time
from functools import wraps
from typing import Optional, Callable
import sys


def log_progress(message: str, level: str = "INFO", end: str = '\n'):
    """
    统一的日志输出
    
    Args:
        message: 日志消息
        level: 日志级别 (INFO, WARN, ERROR)
        end: 行结束符
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # 根据级别设置颜色（如果支持）
    color_codes = {
        "INFO": "\033[0m",    # 默认
        "WARN": "\033[33m",   # 黄色
        "ERROR": "\033[31m"   # 红色
    }
    reset = "\033[0m"
    
    # 检查是否支持颜色输出
    use_color = sys.stdout.isatty()
    
    if use_color and level in color_codes:
        print(f"[{timestamp}] {color_codes[level]}[{level}]{reset} {message}", end=end)
    else:
        print(f"[{timestamp}] [{level}] {message}", end=end)
    
    # 强制刷新输出
    sys.stdout.flush()


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍数增长
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        log_progress(
                            f"请求失败: {str(e)}，{current_delay:.1f}秒后重试... "
                            f"({attempt + 1}/{max_retries})",
                            "WARN"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            # 如果所有重试都失败了
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def format_time(seconds: float) -> str:
    """
    将秒数格式化为时间字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串 (如 "01:23:45")
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_size(bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        bytes: 字节数
        
    Returns:
        格式化的大小字符串 (如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


def estimate_processing_time(char_count: int) -> float:
    """
    估算处理时间
    
    Args:
        char_count: 字符数
        
    Returns:
        预估的处理时间（秒）
    """
    # 基于经验值：平均每1000字符需要2-3秒
    return (char_count / 1000) * 2.5


def validate_file_path(file_path: str, must_exist: bool = True, extensions: Optional[list] = None) -> bool:
    """
    验证文件路径
    
    Args:
        file_path: 文件路径
        must_exist: 是否必须存在
        extensions: 允许的文件扩展名列表
        
    Returns:
        是否有效
    """
    from pathlib import Path
    
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if extensions and path.suffix.lower() not in extensions:
        raise ValueError(f"不支持的文件格式: {path.suffix}")
    
    return True


# 自定义异常类
class SRT2VoiceError(Exception):
    """SRT2Voice基础异常类"""
    pass


class ConfigError(SRT2VoiceError):
    """配置相关错误"""
    pass


class TTSError(SRT2VoiceError):
    """TTS调用相关错误"""
    pass


class AudioError(SRT2VoiceError):
    """音频处理相关错误"""
    pass


class ParseError(SRT2VoiceError):
    """文件解析相关错误"""
    pass