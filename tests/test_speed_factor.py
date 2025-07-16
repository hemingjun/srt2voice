#!/usr/bin/env python3
"""测试GPT-SoVITS的speed_factor参数效果"""
import time
import requests
import json
from pydub import AudioSegment
import io

def wait_for_service(url, timeout=30):
    """等待服务启动"""
    print(f"等待GPT-SoVITS服务启动...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/", timeout=1)
            if response.status_code < 500:
                print("服务已启动")
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_speed_factor():
    # API配置
    api_url = 'http://127.0.0.1:9880'
    
    # 确保服务已启动
    if not wait_for_service(api_url):
        print("服务启动超时")
        return
    
    # 测试文本 - 使用较短的文本以便对比
    test_text = '今天天气真好。'
    
    # 使用指定的参考音频
    ref_audio_path = '/Users/mingjun/Documents/Claude Project/srt2speech/config/reference_audio/reference_8s.wav'
    ref_text = '爱尔兰是全球顶级的高尔夫圣地，这里有超过400个球场，凯特琳城堡球'
    
    # 基础参数
    base_params = {
        'text': test_text,
        'text_lang': 'zh',
        'ref_audio_path': ref_audio_path,
        'prompt_text': ref_text,
        'prompt_lang': 'zh',
        'top_k': 2,
        'top_p': 0.5,
        'temperature': 0.2,
        'seed': 2024  # 固定种子以减少变化
    }
    
    # 测试不同的speed_factor
    speed_tests = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    results = {}
    
    print(f"\n测试文本: '{test_text}'")
    print("=" * 50)
    
    for speed in speed_tests:
        print(f"\n测试 speed_factor = {speed}")
        
        # 设置speed_factor
        params = base_params.copy()
        params['speed_factor'] = speed
        
        try:
            # 发送请求
            start_time = time.time()
            response = requests.post(f"{api_url}/tts", json=params, timeout=30)
            request_time = time.time() - start_time
            
            if response.status_code == 200:
                # 解析音频
                audio = AudioSegment.from_wav(io.BytesIO(response.content))
                duration = len(audio) / 1000.0
                results[speed] = duration
                
                print(f"  ✓ 成功")
                print(f"  请求耗时: {request_time:.2f}秒")
                print(f"  音频时长: {duration:.2f}秒")
                
                # 保存音频文件
                output_file = f"/tmp/test_speed_{speed}.wav"
                audio.export(output_file, format="wav")
                print(f"  保存到: {output_file}")
                
            else:
                print(f"  ✗ 请求失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"  错误详情: {error_detail}")
                except:
                    print(f"  响应内容: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print(f"  ✗ 请求超时")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    # 分析结果
    if results:
        print("\n" + "=" * 50)
        print("分析结果:")
        
        if 1.0 in results:
            base_duration = results[1.0]
            print(f"\n基准时长 (speed_factor=1.0): {base_duration:.2f}秒")
            print("\n速度因子 vs 实际效果:")
            
            for speed in sorted(results.keys()):
                duration = results[speed]
                expected_duration = base_duration / speed  # 期望的时长
                actual_ratio = base_duration / duration if duration > 0 else 0  # 实际的加速比
                
                print(f"  speed_factor={speed:3.1f}: ")
                print(f"    实际时长: {duration:.2f}秒")
                print(f"    期望时长: {expected_duration:.2f}秒")
                print(f"    实际加速: {actual_ratio:.2f}x")
                print(f"    偏差: {abs(actual_ratio - speed)/speed*100:.1f}%")

if __name__ == "__main__":
    test_speed_factor()