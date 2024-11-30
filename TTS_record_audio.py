import pyaudio
import numpy as np
import time
import io
import wave  # 添加 wave 模块的导入

# 音频设置
CHUNK = 1024  # 每个缓冲区的音频帧数
FORMAT = pyaudio.paInt16  # 采样位深，16位
CHANNELS = 1  # 单声道
RATE = 16000  # 采样率，16kHz
SILENCE_THRESHOLD = 500  # 静默检测阈值
SILENCE_DURATION = 3  # 静默持续时长 (秒)

async def record_audio():
    """异步录制音频并返回音频数据"""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    silent_start_time = None
    has_sound = False  # 记录是否有有效声音输入

    while True:
        data = stream.read(CHUNK)
        frames.append(data)

        # 将数据转换为 numpy 数组进行音量检测
        audio_data = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio_data).mean()

        if volume < SILENCE_THRESHOLD:
            if silent_start_time is None:
                silent_start_time = time.time()  # 记录开始静默的时间
            
            # 计算静默的持续时间
            silent_duration = time.time() - silent_start_time
            if silent_duration >= SILENCE_DURATION:
                break
        else:
            has_sound = True
            silent_start_time = None  # 检测到声音，重置静默计时

    # 停止录音并关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()

    if not has_sound:
        return None

    # 将录音数据存储到内存中的 BytesIO 对象
    audio_buffer = io.BytesIO()
    wf = wave.open(audio_buffer, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    audio_buffer.seek(0)  # 返回到开头
    return audio_buffer  # 返回音频数据流
