import os
import numpy as np
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from TTS_record_audio import record_audio
import asyncio
import logging
from TTS_audio_state import audio_state  # 引入音频状态管理

# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 获取当前工作目录
current_dir = os.getcwd()

# 模型目录
model_dir = os.path.join(current_dir, "SenseVoiceSmall")
vad_model_dir = os.path.join(current_dir, "speech_fsmn_vad_zh-cn-16k-common-pytorch")

# 初始化模型
model = AutoModel(
    model=model_dir,
    trust_remote_code=False,
    disable_update=True,
    vad_model=vad_model_dir,
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
)

print(f"模型已加载: {model}")

async def transcribe_audio(audio_buffer):
    """异步使用 FunASR 模型从音频数据流中提取文本"""
    try:
        # 如果是bytes类型，转换为BytesIO对象
        if isinstance(audio_buffer, bytes):
            import io
            audio_buffer = io.BytesIO(audio_buffer)
            
        audio_data = np.frombuffer(audio_buffer.getvalue(), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / np.iinfo(np.int16).max  # 归一化处理
        res = model.generate(
            input=audio_data,
            cache={},
            language="auto",
            use_itn=True,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=15,
        )
        text = rich_transcription_postprocess(res[0]["text"])
        return text
    except Exception as e:
        logger.error(f"语音识别出错: {e}")
        return None

# async def main():
#     """主函数，控制音频录制和转录的流程"""
#     while True:
#         print()
#         print("Funasr..............................")
#         print("等待语音输入......")

#         # 停止当前音频播放
#         with audio_state.sound_lock:
#             if audio_state.current_sound is not None:
#                 audio_state.current_sound.stop()

#         audio_buffer = await record_audio()  # 录制音频
#         if audio_buffer is not None:
#             text = await transcribe_audio(audio_buffer)  # 识别音频
#             print(text)  # 输出识别结果
#         else:
#             print("没有检测到有效声音输入，重试...")

# if __name__ == "__main__":
#     asyncio.run(main())
