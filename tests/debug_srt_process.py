#!/usr/bin/env python3
"""调试SRT处理流程"""
import logging
from src.config import ConfigManager
from src.parser.srt import SRTParser
from src.audio.processor import AudioProcessor
from src.tts.gptsovits import GPTSoVITSService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 加载配置
config = ConfigManager()
service_config = config.get_service_config('gpt_sovits')

# 创建服务
tts_service = GPTSoVITSService(service_config)

# 解析SRT
parser = SRTParser()
entries = parser.parse('tests/test_srt/golf_test.srt')

# 只处理前3个字幕
entries = entries[:3]

# 创建音频处理器
audio_config = {'max_speed_factor': 2.0, 'fade_duration': 0.05, 'enable_smart_split': True}
audio_processor = AudioProcessor('wav', audio_config)

# 准备字幕数据
subtitles = []
for entry in entries:
    subtitles.append({
        'index': entry.index,
        'start': entry.start_time,
        'end': entry.end_time,
        'content': entry.content
    })

print("开始处理字幕...")
print("=" * 60)

# 处理每个字幕
for i, subtitle in enumerate(subtitles):
    print(f"\n字幕 {i+1}:")
    print(f"  文本: {subtitle['content']}")
    print(f"  时间: {subtitle['start']} --> {subtitle['end']}")
    
    # 计算时长
    duration = (subtitle['end'] - subtitle['start']).total_seconds()
    print(f"  可用时长: {duration:.2f}秒")
    
    # 生成音频（不使用speed_factor）
    try:
        audio = tts_service.text_to_speech(subtitle['content'])
        actual_duration = len(audio) / 1000.0
        print(f"  生成时长: {actual_duration:.2f}秒")
        print(f"  时长比例: {actual_duration/duration:.2f}x")
        
        # 如果需要加速
        if actual_duration > duration:
            speed_factor = actual_duration / duration
            print(f"  需要加速: {speed_factor:.2f}x")
            
            # 重新生成
            audio2 = tts_service.text_to_speech(subtitle['content'], speed_factor=speed_factor)
            actual_duration2 = len(audio2) / 1000.0
            print(f"  加速后时长: {actual_duration2:.2f}秒")
            
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "=" * 60)