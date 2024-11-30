import asyncio
import threading
import logging
from TTS_gptsovits_voice import get_characters_and_emotions, text_to_speech
from TTS_run_model import get_response  # 导入 get_response 函数
from TTS_Funasr import record_audio, transcribe_audio  # 导入录音和转录函数

# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def input_thread(loop):
    """输入线程函数，用于在后台运行事件循环"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def input_loop(character, emotion):
    """持续接收用户输入并返回AI的响应"""
    logger.info("开始语音输入，请说话，输入'退出'结束程序：")
    while True:
        audio_buffer = await record_audio()  # 获取用户的语音输入
        if audio_buffer is not None:
            user_input = await transcribe_audio(audio_buffer)  # 转录音频为文本
            logger.info(f"用户输入: {user_input}")

            if user_input.lower() == '退出。':
                logger.info("退出程序。")
                break
            
            # 获取AI响应
            logger.info("\n正在调用模型生成回复...")
            response = await get_response(user_input)  # 使用异步获取AI的回复
            logger.info(f"AI回复: {response}")

            # 使用TTS模块进行语音播放
            logger.info("\n生成的模型回复将以语音输出...")
            await text_to_speech(response, character, emotion)
        else:
            logger.info("没有检测到有效声音输入，重试...")

async def main():
    """主函数，接受用户输入并启动TTS流程"""
    
    # 初始化角色和情感字典
    characters_and_emotions_dict = get_characters_and_emotions()
    
    # 列出角色
    character_names = list(characters_and_emotions_dict.keys())
    logger.info(f"\n可用角色：{character_names}")
    
    # 用户选择角色
    character = input("选择角色（按回车键选择默认角色）：")
    if character not in character_names:
        character = character_names[0] if character_names else ""
    
    # 用户选择情感
    emotion_options = characters_and_emotions_dict.get(character, ["default"])
    logger.info(f"\n{character} 可用情感：{emotion_options}")
    
    emotion = input("选择情感（按回车键选择默认情感）：")
    if emotion not in emotion_options:
        emotion = "default"
        
    # 启动输入循环
    await input_loop(character, emotion)

if __name__ == "__main__":
    # 创建事件循环
    loop = asyncio.new_event_loop()
    # 启动输入线程
    thread = threading.Thread(target=input_thread, args=(loop,))
    thread.start()
    # 运行主函数
    asyncio.run(main())
    # 停止输入线程
    loop.call_soon_threadsafe(loop.stop)
    thread.join()
