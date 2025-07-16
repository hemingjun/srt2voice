#!/usr/bin/env python3
"""调试文本分割问题"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config
from src.tts.gptsovits import GPTSoVITSService
import logging

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_text_processing():
    """测试文本处理"""
    
    # 加载配置
    config = load_config('config/default.yaml')
    
    # 测试文本
    test_text = "南卡罗来纳是高尔夫天堂，距海岸40分钟处"
    
    print(f"\n测试文本: {test_text}")
    print(f"文本长度: {len(test_text)} 字符")
    
    # 查看配置参数
    voice_settings = config.services['gpt_sovits']['voice_settings']
    print(f"\n当前配置:")
    print(f"- text_split_method: {voice_settings.get('text_split_method', 'not set')}")
    print(f"- speed_factor: {voice_settings.get('speed_factor', 'not set')}")
    print(f"- language: {voice_settings.get('language', 'not set')}")
    print(f"- temperature: {voice_settings.get('temperature', 'not set')}")
    print(f"- top_k: {voice_settings.get('top_k', 'not set')}")
    print(f"- top_p: {voice_settings.get('top_p', 'not set')}")
    
    # 创建服务并测试
    try:
        service = GPTSoVITSService(config.services['gpt_sovits'])
        
        print("\n正在生成音频...")
        audio = service.text_to_speech(test_text)
        
        duration = len(audio) / 1000.0
        print(f"\n生成结果:")
        print(f"- 音频时长: {duration:.2f} 秒")
        print(f"- 预期时长: 约 4 秒")
        print(f"- 时长比例: {duration / 4:.2f}x")
        
        # 保存音频以便分析
        output_path = "tests/debug_output.wav"
        audio.export(output_path, format="wav")
        print(f"\n音频已保存到: {output_path}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_processing()