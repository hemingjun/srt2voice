#!/usr/bin/env python3
"""播放Gemini声音样本"""

import subprocess
import sys
from pathlib import Path
import time

def play_samples():
    output_dir = Path("tests/output/gemini_voices")
    
    # 获取所有生成的音频文件
    audio_files = sorted(output_dir.glob("*.wav"))
    
    if not audio_files:
        print("没有找到音频文件")
        return
    
    print("播放Gemini声音样本")
    print("=" * 50)
    print("请仔细听每个声音，找出与第二句话相同的声音")
    print("=" * 50)
    
    for audio_file in audio_files:
        voice_name = audio_file.stem.split('_')[1]
        print(f"\n播放: {voice_name}")
        
        if sys.platform == "darwin":  # macOS
            subprocess.run(["afplay", str(audio_file)])
        elif sys.platform == "linux":
            subprocess.run(["aplay", str(audio_file)])
        elif sys.platform == "win32":
            subprocess.run(["start", str(audio_file)], shell=True)
        
        time.sleep(1)  # 声音之间暂停1秒
    
    print("\n" + "=" * 50)
    print("播放完成！")
    print("\n可用的声音：")
    for audio_file in audio_files:
        voice_name = audio_file.stem.split('_')[1]
        print(f"  - {voice_name}")

if __name__ == "__main__":
    play_samples()