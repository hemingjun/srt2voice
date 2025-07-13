#!/usr/bin/env python3
"""测试音频重叠处理功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pydub import AudioSegment
from src.config import ConfigManager
from src.parser.srt import SRTParser
from src.audio.processor import AudioProcessor


def create_test_audio(duration_seconds: float, text: str) -> AudioSegment:
    """创建一个测试音频片段（使用静音代替实际TTS）"""
    # 为了测试，我们创建一个指定时长的静音音频
    # 在实际使用中，这里会是TTS生成的音频
    return AudioSegment.silent(duration=int(duration_seconds * 1000))


def test_overlap_handling():
    """测试不同的重叠处理策略"""
    print("=" * 60)
    print("音频重叠处理测试")
    print("=" * 60)
    
    # 解析测试SRT文件
    parser = SRTParser()
    srt_file = "tests/test_srt/overlap_test.srt"
    entries = parser.parse_file(srt_file)
    
    print(f"\n解析了 {len(entries)} 条字幕")
    
    # 测试不同的处理策略
    strategies = ['speed_adjust', 'truncate', 'warn_only']
    
    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"测试策略: {strategy}")
        print("="*60)
        
        # 创建配置
        config = {
            'overlap_handling': strategy,
            'speed_adjust_limit': 1.5,
            'fade_duration': 0.05
        }
        
        # 初始化音频处理器
        processor = AudioProcessor(config=config)
        
        # 模拟音频生成和添加
        audio_durations = [3.0, 2.5, 3.5, 2.0, 1.5, 3.0]  # 模拟的音频时长
        
        for i, entry in enumerate(entries):
            # 创建模拟音频
            audio = create_test_audio(audio_durations[i], entry.content)
            
            # 计算时间参数
            start_time = entry.start_time.total_seconds()
            end_time = entry.end_time.total_seconds()
            next_start_time = None
            
            if i < len(entries) - 1:
                next_start_time = entries[i + 1].start_time.total_seconds()
            
            available_time = end_time - start_time
            if next_start_time:
                available_time = min(available_time, next_start_time - start_time)
            
            print(f"\n字幕 {i+1}:")
            print(f"  文本: {entry.content[:30]}...")
            print(f"  时间窗口: {start_time:.1f}s - {end_time:.1f}s")
            print(f"  音频时长: {audio_durations[i]}s")
            print(f"  可用时长: {available_time:.1f}s")
            
            if audio_durations[i] > available_time:
                print(f"  ⚠️  检测到重叠: {audio_durations[i] - available_time:.1f}s")
            
            # 添加到处理器
            processor.add_audio_segment(
                start_time,
                audio,
                end_time=end_time,
                next_start_time=next_start_time
            )
        
        # 显示统计信息
        stats = processor.get_overlap_statistics()
        print(f"\n统计信息:")
        print(f"  总重叠数: {stats['total_overlaps']}")
        print(f"  速度调整: {stats['speed_adjusted']}")
        print(f"  截断处理: {stats['truncated']}")
        print(f"  仅警告: {stats['warned_only']}")
        print(f"  最大速度: {stats['max_speed_factor']}x")
        print(f"  调整时间: {stats['total_time_adjusted']:.1f}s")


def test_audio_speed_adjustment():
    """测试音频速度调整功能"""
    print("\n" + "="*60)
    print("音频速度调整测试")
    print("="*60)
    
    # 创建测试音频
    original = AudioSegment.silent(duration=3000)  # 3秒
    
    processor = AudioProcessor()
    
    # 测试不同的速度因子
    speed_factors = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    
    for factor in speed_factors:
        adjusted = processor._adjust_audio_speed(original, factor)
        duration = len(adjusted) / 1000.0
        expected = 3.0 / factor
        print(f"速度因子 {factor}x: 原始3.0s → 调整后{duration:.2f}s (预期{expected:.2f}s)")


if __name__ == "__main__":
    print("开始测试音频重叠处理功能...\n")
    
    # 测试重叠处理
    test_overlap_handling()
    
    # 测试速度调整
    test_audio_speed_adjustment()
    
    print("\n测试完成！")