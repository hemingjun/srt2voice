"""测试 GPT-SoVITS 自动启动功能"""
import sys
import os
import time
import yaml
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tts.gptsovits import GPTSoVITSService


def test_auto_start():
    """测试自动启动功能"""
    
    # 创建测试配置
    config = {
        'credentials': {
            'api_url': 'http://127.0.0.1:9880',
            'api_version': 'v2'
        },
        'auto_start': {
            'enabled': True,
            'gpt_sovits_path': '/Users/mingjun/Documents/Git Project/GPT-SoVITS',
            'startup_timeout': 30,
            'use_command_script': True
        },
        'voice_settings': {
            'language': 'zh',
            'ref_audio_path': '/path/to/reference.wav',  # 需要替换为实际路径
            'prompt_text': '这是一段参考音频的文本',
            'prompt_lang': 'zh'
        }
    }
    
    print("测试配置:")
    print(yaml.dump(config, allow_unicode=True))
    
    try:
        print("\n正在初始化 GPT-SoVITS 服务（自动启动已启用）...")
        service = GPTSoVITSService(config)
        
        print("\n服务初始化成功！")
        print("正在测试TTS功能...")
        
        # 测试简单的文本转语音
        test_text = "你好，这是一个测试。"
        audio = service.text_to_speech(test_text)
        
        if audio and len(audio) > 0:
            print(f"TTS测试成功！生成了 {len(audio)} 毫秒的音频")
        else:
            print("TTS测试失败：未生成音频")
            
        # 等待用户确认
        input("\n按回车键停止服务并退出...")
        
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
        

def test_manual_start():
    """测试手动启动模式（自动启动禁用）"""
    
    config = {
        'credentials': {
            'api_url': 'http://127.0.0.1:9880',
            'api_version': 'v2'
        },
        'auto_start': {
            'enabled': False  # 禁用自动启动
        },
        'voice_settings': {
            'language': 'zh',
            'ref_audio_path': '/path/to/reference.wav',
            'prompt_text': '这是一段参考音频的文本',
            'prompt_lang': 'zh'
        }
    }
    
    print("\n测试手动启动模式（自动启动已禁用）...")
    
    try:
        service = GPTSoVITSService(config)
        print("服务连接成功（需要手动启动GPT-SoVITS）")
    except ConnectionError as e:
        print(f"预期的错误（服务未运行）：{e}")
        

if __name__ == "__main__":
    print("=" * 60)
    print("GPT-SoVITS 自动启动功能测试")
    print("=" * 60)
    
    print("\n选择测试模式:")
    print("1. 测试自动启动")
    print("2. 测试手动启动模式")
    print("3. 两种模式都测试")
    
    choice = input("\n请输入选择 (1/2/3): ").strip()
    
    if choice == '1':
        test_auto_start()
    elif choice == '2':
        test_manual_start()
    elif choice == '3':
        test_auto_start()
        print("\n" + "=" * 60)
        test_manual_start()
    else:
        print("无效的选择")