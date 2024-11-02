CHCP 65001
@echo off 
echo 尝试启动程序，请耐心等待gradio启动，等待十几秒，若未自动弹出浏览器，请手动打开浏览器输入http://127.0.0.1:9868
runtime\python.exe ./webuis/character_manager/webui.py

pause