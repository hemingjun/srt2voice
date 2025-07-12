#!/usr/bin/env python3
"""测试不同的GPT-SoVITS参数组合"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import io
from pydub import AudioSegment
import json


def test_with_params(test_name, params_override):
    """使用指定参数测试"""
    api_url = "http://127.0.0.1:9880/tts"
    
    # 基础参数
    base_params = {
        "text": "你好，这是一个测试。今天天气真好。",
        "text_lang": "zh",
        "ref_audio_path": "/Users/mingjun/Documents/Claude Project/srt2speech/assets/reference_audio/reference_8s.wav",
        "prompt_text": "这是参考音频的文本内容",
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
    
    # 应用覆盖参数
    params = {**base_params, **params_override}
    
    print(f"\n测试: {test_name}")
    print(f"参数变更: {params_override}")
    
    try:
        response = requests.post(api_url, json=params, timeout=30)
        
        if response.status_code == 200:
            audio_data = io.BytesIO(response.content)
            audio = AudioSegment.from_wav(audio_data)
            duration = len(audio) / 1000
            
            print(f"✓ 成功 - 音频时长: {duration:.3f}秒")
            
            # 保存较长的音频
            if duration > 1.0:
                filename = f"test_{test_name.replace(' ', '_')}.wav"
                audio.export(filename, format="wav")
                print(f"  已保存到: {filename}")
            
            return duration
        else:
            print(f"✗ 失败 - 状态码: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return 0


def main():
    print("=" * 60)
    print("GPT-SoVITS 参数测试")
    print("=" * 60)
    
    # 测试不同的参数组合
    tests = [
        ("默认参数", {}),
        
        # 不同的prompt_text
        ("通用提示文本", {"prompt_text": "这是一段中文语音。"}),
        ("空提示文本", {"prompt_text": ""}),
        ("数字提示", {"prompt_text": "一二三四五六七八九十"}),
        
        # 不同的text_split_method
        ("不分割文本", {"text_split_method": "cut0"}),
        ("按句号分割", {"text_split_method": "cut1"}),
        
        # 不同的temperature
        ("低温度0.3", {"temperature": 0.3}),
        ("高温度1.5", {"temperature": 1.5}),
        
        # 组合参数
        ("稳定模式", {
            "text_split_method": "cut0",
            "temperature": 0.3,
            "top_k": 3,
            "top_p": 0.7
        }),
        
        # 不同语速
        ("慢速0.8", {"speed_factor": 0.8}),
        ("快速1.2", {"speed_factor": 1.2}),
    ]
    
    results = []
    for test_name, params in tests:
        duration = test_with_params(test_name, params)
        results.append((test_name, duration))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print("-" * 60)
    
    for test_name, duration in results:
        status = "✓" if duration > 1.0 else "✗"
        print(f"{status} {test_name}: {duration:.3f}秒")
    
    # 找出最好的结果
    best_test = max(results, key=lambda x: x[1])
    print(f"\n最佳结果: {best_test[0]} ({best_test[1]:.3f}秒)")
    
    print("\n建议:")
    print("1. 如果所有测试都生成短音频，可能是参考音频有问题")
    print("2. 尝试使用GPT-SoVITS自带的示例音频作为参考")
    print("3. 检查GPT-SoVITS的模型是否正确加载")


if __name__ == "__main__":
    main()