"""会话管理工具，用于保持转换过程的一致性"""
import time
import random
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SessionManager:
    """会话管理器，管理单次转换任务的状态"""
    
    def __init__(self):
        """初始化会话管理器"""
        self.session_id: str = self._generate_session_id()
        self.session_seed: Optional[int] = None
        self.start_time: float = time.time()
        self.stats: Dict[str, Any] = {
            'total_subtitles': 0,
            'processed_subtitles': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'audio_adjustments': 0,
            'speed_adjustments': [],
            'warnings': []
        }
        logger.info(f"创建新会话: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        timestamp = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        return f"session_{timestamp}_{random_suffix}"
    
    def get_session_seed(self, config_seed: int = -1) -> int:
        """获取会话种子，确保整个会话使用相同种子
        
        Args:
            config_seed: 配置文件中的种子值，-1表示随机
            
        Returns:
            int: 会话种子
        """
        if self.session_seed is None:
            if config_seed > 0:
                # 使用配置的固定种子
                self.session_seed = config_seed
                logger.info(f"使用配置种子: {self.session_seed}")
            else:
                # 生成会话级随机种子
                self.session_seed = random.randint(1, 999999)
                logger.info(f"生成会话种子: {self.session_seed}")
        
        return self.session_seed
    
    def update_stats(self, key: str, value: Any = None) -> None:
        """更新会话统计信息
        
        Args:
            key: 统计项名称
            value: 统计值，如果为None则自增1
        """
        if value is None:
            # 自增计数器
            if key in self.stats and isinstance(self.stats[key], (int, float)):
                self.stats[key] += 1
        elif key == 'speed_adjustments' and isinstance(value, (int, float)):
            # 记录速度调整
            self.stats[key].append(value)
        elif key == 'warnings' and isinstance(value, str):
            # 记录警告信息
            self.stats[key].append(value)
        else:
            # 直接设置值
            self.stats[key] = value
    
    def add_warning(self, warning: str) -> None:
        """添加警告信息
        
        Args:
            warning: 警告信息
        """
        self.stats['warnings'].append(warning)
        logger.warning(warning)
    
    def get_duration(self) -> float:
        """获取会话持续时间（秒）"""
        return time.time() - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """获取会话摘要
        
        Returns:
            Dict: 会话统计摘要
        """
        duration = self.get_duration()
        processed = self.stats['processed_subtitles']
        total = self.stats['total_subtitles']
        
        summary = {
            'session_id': self.session_id,
            'duration_seconds': round(duration, 2),
            'duration_formatted': self._format_duration(duration),
            'progress': f"{processed}/{total}",
            'completion_rate': round(processed / total * 100, 1) if total > 0 else 0,
            'session_seed': self.session_seed,
        }
        
        # 添加缓存统计
        cache_total = self.stats['cache_hits'] + self.stats['cache_misses']
        if cache_total > 0:
            summary['cache_hit_rate'] = round(
                self.stats['cache_hits'] / cache_total * 100, 1
            )
        
        # 添加音频调整统计
        if self.stats['audio_adjustments'] > 0:
            summary['audio_adjustments'] = self.stats['audio_adjustments']
            if self.stats['speed_adjustments']:
                avg_speed = sum(self.stats['speed_adjustments']) / len(self.stats['speed_adjustments'])
                summary['avg_speed_adjustment'] = round(avg_speed, 2)
        
        # 添加警告数量
        if self.stats['warnings']:
            summary['warnings_count'] = len(self.stats['warnings'])
        
        return summary
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时长字符串
        """
        minutes, seconds = divmod(int(seconds), 60)
        if minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def print_summary(self, console) -> None:
        """打印会话摘要到控制台
        
        Args:
            console: Rich控制台对象
        """
        summary = self.get_summary()
        
        console.print("\n[bold cyan]会话统计:[/bold cyan]")
        console.print(f"  会话ID: {summary['session_id']}")
        console.print(f"  处理时长: {summary['duration_formatted']}")
        console.print(f"  处理进度: {summary['progress']} ({summary['completion_rate']}%)")
        console.print(f"  会话种子: {summary['session_seed']}")
        
        if 'cache_hit_rate' in summary:
            console.print(f"  缓存命中率: {summary['cache_hit_rate']}%")
        
        if 'audio_adjustments' in summary:
            console.print(f"  音频调整次数: {summary['audio_adjustments']}")
            if 'avg_speed_adjustment' in summary:
                console.print(f"  平均速度调整: {summary['avg_speed_adjustment']}x")
        
        if 'warnings_count' in summary:
            console.print(f"  [yellow]警告数量: {summary['warnings_count']}[/yellow]")


# 全局会话实例
_current_session: Optional[SessionManager] = None


def get_current_session() -> Optional[SessionManager]:
    """获取当前会话实例"""
    return _current_session


def create_session() -> SessionManager:
    """创建新的会话"""
    global _current_session
    _current_session = SessionManager()
    return _current_session


def clear_session() -> None:
    """清除当前会话"""
    global _current_session
    _current_session = None