#!/usr/bin/env python3
"""测试GPT-SoVITS生成第一句话"""

import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tts.gptsovits import GPTSoVITSService
from pydub import AudioSegment

def main():
    # 第一句话文本
    text = "有些高尔夫目的地就是与众不同，圣地亚哥就是其中之一。"
    
    # 加载配置
    from src.config import ConfigManager
    config_manager = ConfigManager()
    gpt_sovits_config = config_manager.get_service_config('gpt_sovits').model_dump()
    
    # 创建TTS服务实例
    tts = GPTSoVITSService(gpt_sovits_config)
    
    try:
        # 生成音频
        print(f"正在生成音频: {text}")
        audio_segment = tts.text_to_speech(text)
        
        if audio_segment:
            # 保存音频文件
            output_path = project_root / "tests" / "output" / "first_sentence.wav"
            output_path.parent.mkdir(exist_ok=True)
            
            audio_segment.export(str(output_path), format="wav")
            
            print(f"音频已保存到: {output_path}")
            
            # 播放音频
            print("正在播放音频...")
            if sys.platform == "darwin":  # macOS
                subprocess.run(["afplay", str(output_path)])
            elif sys.platform == "linux":
                subprocess.run(["aplay", str(output_path)])
            elif sys.platform == "win32":
                subprocess.run(["start", str(output_path)], shell=True)
            
            print("播放完成！")
        else:
            print("音频生成失败")
            
    finally:
        # 清理资源
        print("正在清理资源...")
        tts._cleanup()

if __name__ == "__main__":
    main()