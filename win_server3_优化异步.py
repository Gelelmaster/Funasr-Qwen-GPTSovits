import asyncio
import logging
import os
import json
# from TTS_gptsovits_voice import text_to_speech
from TTS_gptsovits_voice import text_to_speech
from TTS_run_model import get_response

# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 存储当前连接的客户端
clients = []
# 用于判断是否所有客户端都已断开连接
shutdown_flag = False
# 服务端是否正在关闭的标志
server_shutting_down = False

def load_character_and_emotion():
    """读取角色和情感列表"""
    character_data = {}
    base_dir = 'trained'
    for root, dirs, files in os.walk(base_dir):
        if 'infer_config.json' in files:
            character_name = os.path.basename(root)
            config_file = os.path.join(root, 'infer_config.json')
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    emotion_list = list(config.get('emotion_list', {}).keys())
                    character_data[character_name] = emotion_list
            except Exception as e:
                logger.error(f"Error loading {config_file}: {e}")
    return character_data

async def handle_client(reader, writer):
    """处理客户端的消息并生成AI响应"""
    addr = writer.get_extra_info('peername')
    clients.append(writer)
    
    try:
        logger.info(f"新连接来自 {addr}")
        
        while True:
            try:
                data = await reader.read(1024)
                if not data:
                    break
                
                message = data.decode('utf-8')
                logger.info(f"收到消息: {message}")

                character, emotion, content = message.split(',', 2)
                
                # 处理系统命令
                if character == "SYSTEM" and emotion == "COMMAND":
                    if content == "LIST_CHARACTERS":
                        character_data = load_character_and_emotion()
                        response = json.dumps(character_data)
                        writer.write(response.encode('utf-8'))
                        await writer.drain()
                        continue
                    elif content == "DISCONNECT":
                        logger.info(f"客户端 {addr} 请求断开连接")
                        break
                    else:
                        logger.warning(f"收到未知命令: {content}")
                        continue
                
                # 处理普通消息
                logger.info(f"角色: {character}, 情感: {emotion}, 消息: {content}")
                
                # 获取AI响应
                response = await get_response(content)
                logger.info(f"AI回复: {response}")
                
                # 使用TTS生成语音
                await text_to_speech(response, character, emotion)
                
                # 发送响应给客户端
                writer.write(response.encode('utf-8'))
                await writer.drain()

            except ValueError:
                logger.error("从客户端收到的消息格式无效")
                continue
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                continue

    except Exception as e:
        logger.error(f"处理客户端 {addr} 时出错: {e}")
    finally:
        logger.info(f"关闭与 {addr} 的连接")
        if writer in clients:
            clients.remove(writer)
        writer.close()
        await writer.wait_closed()

        global shutdown_flag
        if len(clients) == 0:
            shutdown_flag = True

async def main():
    """创建并启动服务器"""
    global server_shutting_down
    
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', 5555
    )
    
    addr = server.sockets[0].getsockname()
    logger.info(f'服务器正在监听 {addr}...')

    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器正在关闭...")
        server_shutting_down = True
        # 等待所有客户端断开连接
        while not shutdown_flag and len(clients) > 0:
            await asyncio.sleep(1)
    finally:
        for writer in clients:
            writer.close()
            await writer.wait_closed()
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已关闭")