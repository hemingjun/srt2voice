#!/usr/bin/env python3
"""准备GPT-SoVITS参考音频"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydub import AudioSegment

def prepare_reference_audio(input_path, output_path, duration_seconds=8):
    """
    准备符合GPT-SoVITS要求的参考音频（3-10秒）
    
    Args:
        input_path: 输入音频路径
        output_path: 输出音频路径
        duration_seconds: 目标时长（秒）
    """
    print(f"正在处理音频文件：{input_path}")
    
    # 加载音频
    audio = AudioSegment.from_file(input_path)
    
    # 获取原始时长
    original_duration = len(audio) / 1000  # 转换为秒
    print(f"原始音频时长：{original_duration:.1f}秒")
    
    # 截取指定时长
    target_duration_ms = duration_seconds * 1000
    if len(audio) > target_duration_ms:
        audio = audio[:target_duration_ms]
        print(f"已截取前{duration_seconds}秒")
    else:
        print(f"音频时长已经小于{duration_seconds}秒，保持原样")
    
    # 导出为WAV格式（GPT-SoVITS推荐格式）
    audio.export(output_path, format="wav")
    print(f"已保存到：{output_path}")
    
    # 验证输出时长
    output_audio = AudioSegment.from_wav(output_path)
    output_duration = len(output_audio) / 1000
    print(f"输出音频时长：{output_duration:.1f}秒")
    
    if 3 <= output_duration <= 10:
        print("✓ 音频时长符合GPT-SoVITS要求（3-10秒）")
    else:
        print("✗ 警告：音频时长不在3-10秒范围内")


if __name__ == "__main__":
    # 准备参考音频
    input_file = "assets/reference_audio/reference_audio.mp3"
    output_file = "assets/reference_audio/reference_8s.wav"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    prepare_reference_audio(input_file, output_file, duration_seconds=8)
    
    print("\n请更新您的配置文件，使用新的参考音频：")
    print(f"ref_audio_path: {os.path.abspath(output_file)}")