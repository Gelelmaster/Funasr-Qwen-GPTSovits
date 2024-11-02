# Gptsovit-tts.py

import io
import numpy as np
import logging
import soundfile as sf
from pygame import mixer
from Synthesizers.base import Base_TTS_Synthesizer, Base_TTS_Task
from importlib import import_module
from src.common_config_manager import app_config
import torch
import asyncio
import threading

# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 设定日志级别
for logger_name in ["markdown_it", "urllib3", "httpcore", "httpx", "asyncio", "charset_normalizer", "torchaudio._extension"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# 检查CUDA可用性
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"\nUsing {'GPU' if torch.cuda.is_available() else 'CPU'} for inference.")

# 动态导入语音合成器模块
synthesizer_name = app_config.synthesizer
synthesizer_module = import_module(f"Synthesizers.{synthesizer_name}")
TTS_Synthesizer = synthesizer_module.TTS_Synthesizer
TTS_Task = synthesizer_module.TTS_Task

# 创建合成器实例
tts_synthesizer: Base_TTS_Synthesizer = TTS_Synthesizer(debug_mode=True)

# 初始化音频播放库
mixer.init()
characters_and_emotions_dict = {}

# 当前音频播放对象和锁
current_sound = None
sound_lock = threading.Lock()

def get_characters_and_emotions():
    """获取角色和情感信息"""
    global characters_and_emotions_dict
    if not characters_and_emotions_dict:
        characters_and_emotions_dict = tts_synthesizer.get_characters()
    return characters_and_emotions_dict

# Gptsovit_tts.py

async def get_audio(data, streaming=False):
    """生成音频数据"""
    if not data.get("text"):
        raise ValueError("文本不能为空")

    try:
        # 确保 task 在设备上
        task: Base_TTS_Task = tts_synthesizer.params_parser(data)
        
        # 将任务中的每一个张量都移动到指定设备上
        if hasattr(task, 'to'):
            task = task.to(device)
        else:
            logger.error("任务不支持移动到设备")
        
        # 检查生成器输出
        gen = tts_synthesizer.generate(task, return_type="numpy")

        if not streaming:
            audio_data = next(gen)
            logger.info(f"\n生成的音频数据（元组）: {audio_data}, 长度: {len(audio_data)}")
            return audio_data
        else:
            # 流式音频，逐块返回
            return b''.join(chunk for chunk in gen)

    except Exception as e:
        logger.error(f"\n错误: {e}")
        raise RuntimeError(f"\n错误: {e}")


async def play_audio(audio_data, sample_rate=32000):
    """播放生成的音频数据"""
    global current_sound

    logger.info(f"\n音频数据类型: {type(audio_data)}, 长度: {len(audio_data)}")

    if isinstance(audio_data, tuple):
        sample_rate, audio_data = audio_data
        logger.info(f"\n提取音频数据: {audio_data}, 采样率: {sample_rate}")

    audio_data = np.array(audio_data)

    if audio_data.ndim == 1:
        audio_data = audio_data.reshape(-1, 1)
    elif audio_data.ndim > 2:
        raise ValueError("不支持的音频数据维度")

    audio_buffer = io.BytesIO()
    sf.write(audio_buffer, audio_data, sample_rate, format='WAV')
    audio_buffer.seek(0)

    with sound_lock:
        if current_sound is not None:
            current_sound.stop()
        current_sound = mixer.Sound(audio_buffer)
        current_sound.play()

    while mixer.get_busy():
        await asyncio.sleep(0.1)

def play_audio_sync(audio_data, sample_rate=32000):
    """同步播放生成的音频数据"""
    asyncio.run(play_audio(audio_data, sample_rate))

async def text_to_speech(text, character="", emotion="default"):
    """文本转语音流程"""
    data = {"text": text, "character": character, "emotion": emotion}

    logger.info("\n开始生成音频...")
    audio_data = await get_audio(data)
    logger.info("\n生成完成，正在播放音频...")
    threading.Thread(target=play_audio_sync, args=(audio_data,)).start()
