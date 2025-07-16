#!/usr/bin/env python3
"""测试GPT-SoVITS的speed_factor参数"""
import time
from pydub import AudioSegment
from src.config import ConfigManager
from src.tts.gptsovits import GPTSoVITSService

def test_speed_factor():
    # 初始化配置
    config = ConfigManager()
    
    # 获取GPT-SoVITS配置
    service_config = config.services.get('gpt_sovits')
    if not service_config:
        print("GPT-SoVITS配置不存在")
        return
    
    # 创建服务实例
    service = GPTSoVITSService(service_config)
    
    # 测试文本
    test_text = "这是一个测试句子。"
    
    # 测试不同的speed_factor
    speed_tests = [1.0, 1.5, 2.0]
    durations = {}
    
    for speed in speed_tests:
        print(f"\n测试 speed_factor = {speed}")
        
        try:
            # 生成音频
            start_time = time.time()
            audio = service.text_to_speech(test_text, speed_factor=speed)
            gen_time = time.time() - start_time
            
            # 获取音频时长
            duration = len(audio) / 1000.0  # 毫秒转秒
            durations[speed] = duration
            
            print(f"  生成耗时: {gen_time:.2f}秒")
            print(f"  音频时长: {duration:.2f}秒")
            
            if speed != 1.0:
                expected_ratio = 1.0 / speed  # 期望的时长比例
                actual_ratio = duration / durations[1.0]  # 实际的时长比例
                print(f"  期望时长比例: {expected_ratio:.2f}x")
                print(f"  实际时长比例: {actual_ratio:.2f}x")
            
            # 保存音频以便验证
            audio.export(f"/tmp/test_speed_{speed}.wav", format="wav")
            
        except Exception as e:
            print(f"  错误: {e}")
    
    # 分析结果
    print("\n分析结果:")
    if 1.0 in durations:
        base_duration = durations[1.0]
        print(f"基准时长(speed=1.0): {base_duration:.2f}秒")
        for speed, duration in durations.items():
            if speed != 1.0:
                actual_speedup = base_duration / duration
                print(f"speed_factor={speed}: 实际加速{actual_speedup:.2f}x")

if __name__ == "__main__":
    test_speed_factor()