"""音频时长检测测试"""
import unittest
from pydub import AudioSegment
from src.audio.timing import AudioTimingManager


class TestAudioTiming(unittest.TestCase):
    """测试音频时长管理"""
    
    def setUp(self):
        """初始化测试"""
        self.timing_manager = AudioTimingManager()
        # 创建测试音频（3秒）
        self.test_audio = AudioSegment.silent(duration=3000)
    
    def test_no_overlap(self):
        """测试无重叠情况"""
        # 音频3秒，可用时间4秒，不应该有调整
        adjusted_audio, warning = self.timing_manager.check_and_adjust_audio(
            self.test_audio, 0, 4, 1, "测试字幕"
        )
        
        self.assertIsNone(warning)
        self.assertEqual(len(adjusted_audio), len(self.test_audio))
    
    def test_speed_adjustment(self):
        """测试速度调整"""
        # 音频3秒，可用时间2秒，应该加速1.5倍
        adjusted_audio, warning = self.timing_manager.check_and_adjust_audio(
            self.test_audio, 0, 2, 1, "测试字幕"
        )
        
        self.assertIsNotNone(warning)
        self.assertIn("已调速", warning)
        # 调速后应该是2秒
        self.assertAlmostEqual(len(adjusted_audio) / 1000, 2, places=1)
    
    def test_truncation(self):
        """测试截断处理"""
        # 使用截断策略
        timing_manager = AudioTimingManager(overlap_handling='truncate')
        
        # 音频3秒，可用时间2秒，应该截断
        adjusted_audio, warning = timing_manager.check_and_adjust_audio(
            self.test_audio, 0, 2, 1, "测试字幕"
        )
        
        self.assertIsNotNone(warning)
        self.assertIn("已截断", warning)
        # 截断后应该是2秒
        self.assertEqual(len(adjusted_audio) / 1000, 2)
    
    def test_warn_only(self):
        """测试仅警告模式"""
        # 使用仅警告策略
        timing_manager = AudioTimingManager(overlap_handling='warn_only')
        
        # 音频3秒，可用时间2秒，应该只警告不调整
        adjusted_audio, warning = timing_manager.check_and_adjust_audio(
            self.test_audio, 0, 2, 1, "测试字幕"
        )
        
        self.assertIsNotNone(warning)
        self.assertIn("保持原样", warning)
        # 音频长度不变
        self.assertEqual(len(adjusted_audio), len(self.test_audio))


if __name__ == '__main__':
    unittest.main()