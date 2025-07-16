#!/usr/bin/env python3
"""测试问题文本"""
import time
import requests
import json
from pydub import AudioSegment
import io

# 测试各种文本
test_texts = [
    "今天天气真好。",  # 简单文本
    "俯瞰太平洋，南北球场都举办过顶级赛事，但仍向你和你的团队开放。",  # 问题文本
    "从传奇的托里松开始，那里有两个冠军球场与悬崖美景相遇。",  # 另一个文本
]

# API配置
api_url = 'http://127.0.0.1:9880/tts'
ref_audio_path = '/Users/mingjun/Documents/Claude Project/srt2speech/config/reference_audio/reference_8s.wav'
ref_text = '爱尔兰是全球顶级的高尔夫圣地，这里有超过400个球场，凯特琳城堡球'

print("测试不同文本的生成效果")
print("=" * 60)

for text in test_texts:
    print(f"\n测试文本: '{text}'")
    print(f"字数: {len(text)}字")
    
    # 构建请求
    data = {
        'text': text,
        'text_lang': 'zh',
        'ref_audio_path': ref_audio_path,
        'prompt_text': ref_text,
        'prompt_lang': 'zh',
        'top_k': 2,
        'top_p': 0.5,
        'temperature': 0.2,
        'speed_factor': 1.0,
        'seed': 2024
    }
    
    try:
        start_time = time.time()
        response = requests.post(api_url, json=data, timeout=60)
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            audio = AudioSegment.from_wav(io.BytesIO(response.content))
            duration = len(audio) / 1000.0
            
            print(f"✓ 成功")
            print(f"  请求耗时: {request_time:.2f}秒")
            print(f"  音频时长: {duration:.2f}秒")
            print(f"  每字时长: {duration/len(text):.3f}秒/字")
            print(f"  语速: {len(text)*60/duration:.0f}字/分钟")
            
            # 保存音频
            filename = f"/tmp/test_text_{len(text)}.wav"
            audio.export(filename, format="wav")
            print(f"  保存到: {filename}")
            
        else:
            print(f"✗ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 错误: {e}")