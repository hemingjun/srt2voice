#!/usr/bin/env python3
"""调试GPT-SoVITS音频生成问题"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import io
from pydub import AudioSegment
import json


def debug_gptsovits():
    """详细调试GPT-SoVITS服务"""
    
    # API配置
    api_url = "http://127.0.0.1:9880/tts"
    
    # 请求数据
    data = {
        "text": "你好，这是一个测试。",
        "text_lang": "zh",
        "ref_audio_path": "/Users/mingjun/Documents/Claude Project/srt2speech/assets/reference_audio/reference_8s.wav",
        "prompt_text": "这是参考音频的文本内容",  # TODO: 需要更新为实际内容
        "prompt_lang": "zh",
        "top_k": 5,
        "top_p": 1,
        "temperature": 1,
        "speed_factor": 1.0,
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": False
    }
    
    print("=" * 60)
    print("GPT-SoVITS 调试信息")
    print("=" * 60)
    
    print("\n1. 请求参数:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    try:
        # 发送请求
        print("\n2. 发送请求到:", api_url)
        response = requests.post(api_url, json=data, timeout=30)
        
        print(f"\n3. 响应状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            # 分析响应数据
            content_length = len(response.content)
            print(f"\n4. 响应数据大小: {content_length} bytes ({content_length/1024:.2f} KB)")
            
            # 保存原始数据
            raw_path = "debug_raw_response.bin"
            with open(raw_path, "wb") as f:
                f.write(response.content)
            print(f"   原始数据已保存到: {raw_path}")
            
            # 尝试解析为音频
            try:
                audio_data = io.BytesIO(response.content)
                audio = AudioSegment.from_wav(audio_data)
                
                print(f"\n5. 音频解析成功:")
                print(f"   时长: {len(audio)/1000:.3f} 秒")
                print(f"   采样率: {audio.frame_rate} Hz")
                print(f"   声道数: {audio.channels}")
                print(f"   采样宽度: {audio.sample_width} bytes")
                
                # 保存音频
                output_path = "debug_output.wav"
                audio.export(output_path, format="wav")
                print(f"\n   音频已保存到: {output_path}")
                
                # 检查音频内容
                if len(audio) < 1000:  # 小于1秒
                    print("\n⚠️  警告: 音频时长异常短！")
                    print("   可能原因:")
                    print("   1. 参考音频的文本与实际内容不匹配")
                    print("   2. GPT-SoVITS模型未正确加载")
                    print("   3. 文本处理参数需要调整")
                
            except Exception as e:
                print(f"\n❌ 音频解析失败: {e}")
                print("   尝试查看原始数据的前100字节:")
                print(response.content[:100])
                
        else:
            print(f"\n❌ 请求失败:")
            try:
                error_info = response.json()
                print(json.dumps(error_info, indent=2, ensure_ascii=False))
            except:
                print(response.text)
    
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # 建议
    print("\n建议:")
    print("1. 确认参考音频的文本内容是否正确")
    print("   - 播放 reference_8s.wav 并记录实际说的内容")
    print("   - 更新 prompt_text 为实际内容")
    print("\n2. 尝试不同的参数:")
    print("   - text_split_method: 'cut0' (不分割)")
    print("   - temperature: 0.3 (更稳定)")
    print("   - speed_factor: 0.9 (稍慢)")
    print("\n3. 检查GPT-SoVITS服务日志")
    print("   查看服务端是否有错误或警告信息")


if __name__ == "__main__":
    debug_gptsovits()