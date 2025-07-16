#!/usr/bin/env python3
"""调试GPT-SoVITS生成超长音频的问题"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ConfigManager
from src.tts.gptsovits import GPTSoVITSService
import logging

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_long_audio_issue():
    """测试长音频问题"""
    
    # 加载配置
    config_manager = ConfigManager('config/default.yaml')
    config = config_manager.get_service_config('gpt_sovits')
    
    if not config:
        print("错误：无法加载 gpt_sovits 配置")
        return
    
    # 测试文本（第一句字幕）
    test_text = "南卡罗来纳是高尔夫天堂，距海岸40分钟处"
    expected_duration = 4.099  # 秒
    
    print(f"\n=== 测试信息 ===")
    print(f"测试文本: {test_text}")
    print(f"文本长度: {len(test_text)} 字符")
    print(f"预期时长: {expected_duration} 秒")
    
    # 查看关键配置
    voice_settings = config.voice_settings
    print(f"\n=== 当前配置 ===")
    print(f"API版本: {config.api_version}")
    print(f"text_split_method: {voice_settings.get('text_split_method', 'not set')}")
    print(f"speed_factor: {voice_settings.get('speed_factor', 'not set')}")
    print(f"language: {voice_settings.get('language', 'not set')}")
    print(f"temperature: {voice_settings.get('temperature', 'not set')}")
    print(f"top_k: {voice_settings.get('top_k', 'not set')}")
    print(f"top_p: {voice_settings.get('top_p', 'not set')}")
    
    # 测试不同的text_split_method
    split_methods = ['cut0', 'cut1', 'cut2', 'cut3', 'cut4', 'cut5']
    
    for method in split_methods:
        print(f"\n=== 测试 text_split_method: {method} ===")
        
        # 修改配置
        config.voice_settings['text_split_method'] = method
        
        try:
            # 创建服务
            service = GPTSoVITSService(config)
            
            # 生成音频
            print(f"正在生成音频...")
            audio = service.text_to_speech(test_text)
            
            # 计算时长
            actual_duration = len(audio) / 1000.0
            duration_ratio = actual_duration / expected_duration
            
            print(f"生成结果:")
            print(f"- 实际时长: {actual_duration:.2f} 秒")
            print(f"- 时长比例: {duration_ratio:.2f}x")
            
            # 保存有问题的音频
            if duration_ratio > 2.0:
                output_path = f"tests/debug_long_audio_{method}.wav"
                audio.export(output_path, format="wav")
                print(f"- 音频已保存到: {output_path}")
            
            # 停止服务
            service.stop()
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_long_audio_issue()