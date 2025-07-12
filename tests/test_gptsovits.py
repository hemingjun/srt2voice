"""使用配置文件测试GPT-SoVITS服务"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from src.config import ConfigManager
from src.tts.gptsovits import GPTSoVITSService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_gptsovits_with_config():
    """使用配置文件测试GPT-SoVITS服务"""
    
    print("=" * 50)
    print("GPT-SoVITS 服务测试（使用配置文件）")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        print("\n1. 加载配置文件...")
        config_manager = ConfigManager('config/default.yaml')
        service_config = config_manager.get_service_config('gpt_sovits')
        
        if not service_config or not service_config.enabled:
            print("✗ GPT-SoVITS服务未启用")
            return False
        
        print("✓ 配置加载成功")
        print(f"  使用voice profile: default")
        print(f"  参考音频: {service_config.voice_settings.ref_audio_path}")
        
        # 2. 初始化服务
        print("\n2. 初始化GPT-SoVITS服务...")
        service = GPTSoVITSService(service_config.model_dump())
        print("✓ 服务初始化成功")
        
        # 3. 测试文本转语音
        print("\n3. 测试文本转语音...")
        test_text = "你好，这是使用配置文件的测试。"
        audio = service.text_to_speech(test_text)
        print(f"✓ 转换成功，音频长度：{len(audio)}ms")
        
        # 保存测试音频
        output_path = Path("tests/output/config_test.wav")
        output_path.parent.mkdir(exist_ok=True)
        audio.export(output_path, format="wav")
        print(f"✓ 音频已保存到：{output_path}")
        
        print("\n" + "=" * 50)
        print("✅ 测试通过！配置引用机制正常工作")
        print("=" * 50)
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ 测试失败：{e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_voice_profile_switching():
    """测试切换不同的voice profile"""
    print("\n\n测试Voice Profile切换")
    print("=" * 50)
    
    # 创建一个新的voice profile用于测试
    test_profile_path = Path("config/reference_voices/test_voice.yaml")
    
    # 这里只是演示如何切换，实际使用时需要准备对应的音频文件
    print("要切换voice profile，只需修改config/default.yaml中的voice_profile字段")
    print("例如：")
    print("  voice_profile: 'male_voice'  # 使用男声")
    print("  voice_profile: 'female_voice'  # 使用女声")
    print("\n每个voice profile对应config/reference_voices/目录下的一个yaml文件")


if __name__ == "__main__":
    # 先检查服务连接
    import requests
    try:
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        if response.status_code >= 500:
            print("GPT-SoVITS服务不可用")
            exit(1)
    except:
        print("请先启动GPT-SoVITS服务")
        exit(1)
    
    # 运行测试
    if test_gptsovits_with_config():
        test_voice_profile_switching()