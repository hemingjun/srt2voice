"""端到端测试：SRT文件转语音"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from src.config import ConfigManager
from src.parser.srt import SRTParser
from src.tts.gptsovits import GPTSoVITSService
from src.audio.processor import AudioProcessor
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_srt_to_speech():
    """测试完整的SRT转语音流程"""
    
    print("=" * 60)
    print("SRT转语音 端到端测试")
    print("=" * 60)
    
    # 配置
    srt_file = "tests/test_srt/sample.srt"
    output_file = "tests/output/sample_speech.wav"
    
    try:
        # 1. 解析SRT文件
        print("\n1. 解析SRT文件...")
        parser = SRTParser()
        subtitles = parser.parse(srt_file)
        print(f"✓ 解析成功，共 {len(subtitles)} 条字幕")
        
        for i, sub in enumerate(subtitles, 1):
            print(f"   {i}. [{sub.start_time:.1f}s-{sub.end_time:.1f}s] {sub.text}")
        
        # 2. 加载TTS服务配置
        print("\n2. 初始化TTS服务...")
        config_manager = ConfigManager('config/default.yaml')
        service_config = config_manager.get_service_config('gpt_sovits')
        
        if not service_config or not service_config.enabled:
            print("✗ GPT-SoVITS服务未启用")
            return False
        
        tts_service = GPTSoVITSService(service_config.model_dump())
        print("✓ TTS服务初始化成功")
        
        # 3. 转换每条字幕为语音
        print("\n3. 转换字幕为语音...")
        audio_segments = []
        
        for i, subtitle in enumerate(subtitles, 1):
            print(f"\n   处理第 {i}/{len(subtitles)} 条字幕: {subtitle.text}")
            start_time = time.time()
            
            # 生成语音
            audio = tts_service.text_to_speech(subtitle.text)
            
            # 计算需要的静音时长
            if i == 1:
                # 第一条字幕前的静音
                silence_before = AudioSegment.silent(duration=int(subtitle.start_time * 1000))
                audio_segments.append(silence_before)
            elif i > 1:
                # 与前一条字幕之间的静音
                prev_subtitle = subtitles[i-2]
                gap = subtitle.start_time - prev_subtitle.end_time
                if gap > 0:
                    silence = AudioSegment.silent(duration=int(gap * 1000))
                    audio_segments.append(silence)
            
            # 添加语音
            audio_segments.append(audio)
            
            # 统计
            duration = len(audio) / 1000.0
            process_time = time.time() - start_time
            print(f"     ✓ 生成成功: {duration:.1f}秒音频, 耗时{process_time:.1f}秒")
        
        # 4. 合并音频
        print("\n4. 合并音频片段...")
        if audio_segments:
            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio += segment
            
            # 保存输出
            Path(output_file).parent.mkdir(exist_ok=True)
            final_audio.export(output_file, format="wav")
            
            total_duration = len(final_audio) / 1000.0
            print(f"✓ 音频合并成功，总时长: {total_duration:.1f}秒")
            print(f"✓ 保存到: {output_file}")
        else:
            print("✗ 没有音频片段可合并")
            return False
        
        # 5. 验证结果
        print("\n5. 验证结果...")
        output_path = Path(output_file)
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✓ 文件大小: {size_mb:.2f} MB")
            
            # 加载并检查音频
            check_audio = AudioSegment.from_wav(output_file)
            print(f"✓ 采样率: {check_audio.frame_rate} Hz")
            print(f"✓ 声道数: {check_audio.channels}")
            print(f"✓ 时长: {len(check_audio)/1000:.1f} 秒")
        
        print("\n" + "=" * 60)
        print("✅ SRT转语音测试成功！")
        print("=" * 60)
        print(f"\n您可以播放生成的音频文件: {output_file}")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败：{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    # 检查GPT-SoVITS服务
    import requests
    print("检查GPT-SoVITS服务...")
    try:
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        if response.status_code >= 500:
            print("✗ GPT-SoVITS服务不可用")
            print("请先启动服务：")
            print("  cd /path/to/GPT-SoVITS")
            print("  python api_v2.py -a 127.0.0.1 -p 9880")
            return
        print("✓ 服务正常")
    except:
        print("✗ 无法连接到GPT-SoVITS服务")
        print("请先启动服务")
        return
    
    # 运行测试
    test_srt_to_speech()


if __name__ == "__main__":
    main()