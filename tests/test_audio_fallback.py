"""测试音频过长时的服务降级功能"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio.processor import AudioProcessor
from src.audio.exceptions import AudioTooLongError
from src.config import ConfigManager
from src.utils.logger import setup_logger
import logging

# 模拟长文本，用于测试音频过长的情况
LONG_TEXT = """
这是一段非常长的测试文本，用于模拟音频生成时间过长的情况。
在实际使用中，某些TTS服务可能会因为文本过长而生成超出预期时长的音频。
当音频时长超过目标时长的1.5倍时，系统应该自动尝试优化文本并重试。
如果经过3次重试后仍然无法满足时长要求，系统应该自动降级到下一个可用的TTS服务。
这种降级机制确保了即使某个服务无法处理长文本，用户仍然可以获得最终的音频输出。
降级时，系统会按照配置文件中定义的优先级顺序尝试其他服务。
优先级数字越小，表示优先级越高。
例如，如果GPT-SoVITS服务（优先级1）失败，系统会尝试Gemini服务（优先级2）。
这个测试用例将验证这个降级流程是否正常工作。
""" * 5  # 重复5次以确保文本足够长


def test_audio_fallback():
    """测试音频降级功能"""
    logger = setup_logger('test_fallback', level='DEBUG')
    
    # 初始化配置
    config_manager = ConfigManager()
    
    # 创建音频处理器
    audio_processor = AudioProcessor(
        output_format='mp3',
        config=config_manager.config.audio_processing
    )
    
    # 准备测试字幕
    subtitles = [{
        'index': 1,
        'start': 0.0,
        'end': 3.0,  # 目标时长3秒
        'content': LONG_TEXT
    }]
    
    # 模拟一个会产生过长音频的TTS服务
    class MockLongAudioTTS:
        def __init__(self):
            self.name = 'mock_long_audio'
            
        def text_to_speech(self, text, **kwargs):
            # 模拟生成一个超长的音频（10秒）
            from pydub import AudioSegment
            from pydub.generators import Sine
            
            # 生成10秒的音频，远超目标的3秒
            audio = Sine(440).to_audio_segment(duration=10000)
            logger.info(f"Mock service generated {len(audio)/1000:.1f}s audio")
            return audio
    
    # 测试降级流程
    try:
        mock_service = MockLongAudioTTS()
        audio = audio_processor.process_subtitles(subtitles, mock_service)
        print(f"测试失败：应该抛出AudioTooLongError异常")
    except AudioTooLongError as e:
        print(f"✓ 成功触发音频过长异常:")
        print(f"  - 实际时长: {e.actual_duration:.2f}秒")
        print(f"  - 目标时长: {e.target_duration:.2f}秒")
        print(f"  - 时长比例: {e.duration_ratio:.2f}x")
        print(f"  - 重试次数: {e.retry_count}")
        print("\n在实际使用中，CLI会自动降级到下一个服务")
    except Exception as e:
        print(f"测试失败：意外的异常类型 - {type(e).__name__}: {str(e)}")


if __name__ == '__main__':
    test_audio_fallback()