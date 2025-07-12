"""测试Google Gemini TTS服务

重要说明：
1. Gemini API可能返回base64编码的音频数据
2. 我们的实现包含自动检测和解码机制
3. 如果音频输出为噪音，请检查日志中的base64解码信息
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from src.config import ConfigManager
from src.tts.gemini import GeminiTTSService

logging.basicConfig(level=logging.INFO)


def test_gemini_tts():
    """测试Gemini TTS基本功能"""
    
    print("=" * 50)
    print("Google Gemini TTS 服务测试")
    print("=" * 50)
    
    # 确保设置了API密钥
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ 请先设置 GEMINI_API_KEY 环境变量")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        return False
    
    try:
        # 1. 初始化服务
        print("\n1. 初始化Gemini服务...")
        config = {
            'credentials': {
                'api_key': os.getenv('GEMINI_API_KEY')
            },
            'voice_settings': {
                'model': 'gemini-2.5-pro-preview-tts',
                'voice_name': 'Kore',
                'language': 'auto'
            }
        }
        
        service = GeminiTTSService(config)
        print("✓ 服务初始化成功")
        
        # 2. 测试中文
        print("\n2. 测试中文转语音...")
        text_zh = "你好，这是Google Gemini的语音合成测试。"
        audio_zh = service.text_to_speech(text_zh)
        print(f"✓ 中文转换成功，音频长度：{len(audio_zh)}ms")
        
        # 3. 测试英文
        print("\n3. 测试英文转语音...")
        text_en = "Hello, this is a test of Google Gemini text-to-speech."
        audio_en = service.text_to_speech(text_en)
        print(f"✓ 英文转换成功，音频长度：{len(audio_en)}ms")
        
        # 4. 测试中英文混合
        print("\n4. 测试中英文混合...")
        text_mixed = "今天我们来测试Gemini TTS的混合语言支持。"
        audio_mixed = service.text_to_speech(text_mixed)
        print(f"✓ 混合语言转换成功，音频长度：{len(audio_mixed)}ms")
        
        # 5. 测试健康检查
        print("\n5. 测试服务健康检查...")
        is_healthy = service.check_health()
        print(f"✓ 服务健康状态：{'正常' if is_healthy else '异常'}")
        
        # 保存测试音频
        output_dir = Path("tests/output")
        output_dir.mkdir(exist_ok=True)
        
        audio_zh.export(output_dir / "gemini_test_zh.wav", format="wav")
        audio_en.export(output_dir / "gemini_test_en.wav", format="wav")
        audio_mixed.export(output_dir / "gemini_test_mixed.wav", format="wav")
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print(f"音频文件已保存到：{output_dir}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ 测试失败：{e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False


def test_voice_options():
    """测试不同声音选项"""
    print("\n\n测试不同声音选项")
    print("=" * 50)
    
    voices = ['Kore', 'Vale', 'Journey', 'Puck', 'Charon']
    print("可用的声音选项：")
    for voice in voices:
        print(f"  - {voice}")
    
    print("\n要测试不同声音，修改配置中的 voice_name 参数")
    print("建议使用 Kore 作为中文语音")


def test_with_config_file():
    """使用配置文件测试"""
    print("\n\n使用配置文件测试")
    print("=" * 50)
    
    try:
        # 加载配置
        config_manager = ConfigManager('config/default.yaml')
        
        # 检查Gemini服务配置
        if 'gemini' not in config_manager.config.services:
            print("❌ 配置文件中未找到Gemini服务配置")
            return False
        
        gemini_config = config_manager.config.services['gemini']
        print(f"服务名称：{gemini_config.service_name}")
        print(f"优先级：{gemini_config.priority}")
        print(f"是否启用：{gemini_config.enabled}")
        print(f"模型：{getattr(gemini_config.voice_settings, 'model', 'N/A')}")
        print(f"声音：{getattr(gemini_config.voice_settings, 'voice_name', 'N/A')}")
        
        print("\n✓ 配置文件读取成功")
        
    except Exception as e:
        print(f"❌ 配置文件测试失败：{e}")
        return False


def test_different_models():
    """测试不同的模型"""
    print("\n\n测试不同的TTS模型")
    print("=" * 50)
    
    models = [
        ('gemini-2.5-pro-preview-tts', '高质量，适合复杂提示'),
        ('gemini-2.5-flash-preview-tts', '快速，适合日常应用')
    ]
    
    print("可用的TTS模型：")
    for model, desc in models:
        print(f"  - {model}: {desc}")
    
    print("\n注意：这些模型处于预览阶段，可能有使用限制")


if __name__ == "__main__":
    # 运行基本测试
    if test_gemini_tts():
        test_voice_options()
        test_with_config_file()
        test_different_models()
    
    print("\n提示：要在命令行中使用Gemini服务，请运行：")
    print("  export GEMINI_API_KEY='your-api-key'")
    print("  srt2speech input.srt --service gemini")