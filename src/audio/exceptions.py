"""音频处理相关的异常定义"""

class AudioTooLongError(Exception):
    """音频时长超过限制的异常
    
    当音频生成后时长过长，经过多次重试优化仍然无法满足要求时抛出此异常。
    这个异常可以被上层捕获，用于触发TTS服务降级。
    """
    def __init__(self, message: str, actual_duration: float, target_duration: float, retry_count: int):
        super().__init__(message)
        self.actual_duration = actual_duration
        self.target_duration = target_duration
        self.retry_count = retry_count
        self.duration_ratio = actual_duration / target_duration if target_duration > 0 else float('inf')