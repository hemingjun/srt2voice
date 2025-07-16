#!/usr/bin/env python3
"""测试Gemini不同声音选项"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tts.gemini import GeminiTTSService
import os

def test_voices():
    # 测试文本（第二句话）
    text = "查尔斯顿附近的基洼岛，南方优雅与冠军风范的结合。"
    
    # 女声选项
    female_voices = ['Kore', 'Aoede', 'Vale']
    
    # 男声选项  
    male_voices = ['Puck', 'Charon', 'Fenrir']
    
    # 中性声音
    neutral_voices = ['Journey']
    
    all_voices = female_voices + male_voices + neutral_voices
    
    print("测试不同的Gemini声音选项")
    print("=" * 50)
    print(f"测试文本：{text}")
    print("=" * 50)
    
    output_dir = Path("tests/output/gemini_voices")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, voice in enumerate(all_voices, 1):
        print(f"\n{i}. 测试声音: {voice}")
        
        config = {
            'credentials': {
                'api_key': os.getenv('GEMINI_API_KEY', 'AIzaSyDEIjGMiE2hVQZIEpr7qm5W7nmW5eT0puI')
            },
            'voice_settings': {
                'model': 'gemini-2.5-pro-preview-tts',
                'voice_name': voice,
                'language': 'auto'
            }
        }
        
        try:
            service = GeminiTTSService(config)
            audio = service.text_to_speech(text)
            
            # 保存音频
            output_path = output_dir / f"{i:02d}_{voice}.wav"
            audio.export(str(output_path), format="wav")
            
            print(f"   ✓ 已保存到: {output_path.name}")
            
        except Exception as e:
            print(f"   ✗ 生成失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成！请听每个音频文件，找出第二句话使用的声音。")
    print(f"音频文件保存在: {output_dir}")

if __name__ == "__main__":
    test_voices()