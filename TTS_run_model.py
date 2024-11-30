import os
import asyncio
from openai import AsyncOpenAI
import platform
import sys

client = AsyncOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

async def get_response(message):
    """根据用户输入的消息获取AI的响应"""
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": message}],
        model="qwen-plus",
    )
    
    # print(response.model_dump_json())
    # print("_____________")
    content = response.choices[0].message.content
    return content

async def input_loop():
    """持续接收用户输入并返回AI的响应"""
    print("请输入你的问题，输入'退出'结束程序：")
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        user_input = user_input.strip()
        if user_input.lower() == '退出':
            print("退出程序。")
            break
        
        # 获取AI响应
        response = await get_response(user_input)
        print(f"AI回复: {response}")

async def main():
    """主函数，启动输入循环"""
    await input_loop()

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
