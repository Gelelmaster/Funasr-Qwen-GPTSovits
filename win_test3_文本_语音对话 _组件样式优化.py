# 在文件开头添加新的导入
import sys
import socket
import threading
import json
import asyncio
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from TTS_Funasr import transcribe_audio  # 导入语音识别相关功能
from TTS_record_audio import record_audio   # 导入录音相关功能

# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class VoiceInputThread(QThread):
    voice_input_signal = pyqtSignal(str)  # 语音输入信号

    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        asyncio.run(self.input_loop())

    async def input_loop(self):
        while self.is_running:
            try:
                audio_buffer = await record_audio()
                if audio_buffer is not None:
                    user_input = await transcribe_audio(audio_buffer)
                    if user_input:
                        logger.info(f"语音识别结果: {user_input}")
                        self.voice_input_signal.emit(user_input)
            except Exception as e:
                logger.error(f"语音输入错误: {e}")
                continue


class ChatClient(QWidget):
    message_received = pyqtSignal(str)
    connection_closed = pyqtSignal()  # 添加新的信号

    def __init__(self):
        super().__init__()
        self.is_connected = True  # 添加连接状态标志
        self.init_ui()  # 初始化用户界面

        # 连接到服务器
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('127.0.0.1', 5555))  # 假设服务器运行在本地的 127.0.0.1:5555

        # 请求角色和情感数据
        self.request_character_and_emotion()

        # 启动线程以接收服务器的消息
        self.receive_thread = threading.Thread(target=self.receive_message, daemon=True)
        self.receive_thread.start()

        # 初始化语音线程
        self.voice_thread = None

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("聊天程序")  # 设置窗口标题
        self.setGeometry(200, 200, 800, 800)  # 设置窗口大小和位置

        # 窗口居中打开
        # 获取屏幕尺寸和窗口尺寸
        screen = QApplication.primaryScreen()  # 获取主屏幕对象
        screen_geometry = screen.availableGeometry()  # 获取屏幕的可用区域
        screen_center_x = screen_geometry.width() // 2
        screen_center_y = screen_geometry.height() // 2
        window_width = self.width()
        window_height = self.height()
        # 计算窗口左上角坐标，使窗口居中
        x = screen_center_x - (window_width // 2)
        y = screen_center_y - (window_height // 2)
        # 移动窗口到居中位置
        self.move(x, y)

        # 聊天显示区域
        self.chat_area = QScrollArea(self)
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setStyleSheet("""
            QScrollArea {
                background-color: #F5F5F5;
                border: none;
            }
            QScrollArea QScrollBar:vertical {
                width: 10px;  /* 滚动条宽度 */
                background: transparent;
            }
            QScrollArea QScrollBar::handle:vertical {
                background: #CCCCCC;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollArea QScrollBar:vertical:hover {
                width: 12px;  /* 鼠标悬停时增加滚动条宽度 */
                background: rgba(0, 0, 0, 0.1);
            }
            QScrollArea QScrollBar::handle:vertical:hover {
                background: #888888;
            }
            QScrollArea QScrollBar:horizontal {
                height: 0px;
            }
        """)

        # 聊天内容容器
        self.chat_widget = QWidget()
        self.chat_content = QVBoxLayout(self.chat_widget)
        self.chat_content.setAlignment(Qt.AlignTop)
        self.chat_content.setSpacing(10)  # 设置气泡之间的间距
        self.chat_content.setContentsMargins(10, 10, 10, 10)  # 设置内容边距
        self.chat_area.setWidget(self.chat_widget)

        # 初始化角色和情感选择
        self.character_selector = QComboBox(self)  # 角色选择框
        self.character_selector.setStyleSheet("""
            QComboBox {
                font-family: "Microsoft YaHei";
                font-size: 10pt;
                padding: 5px;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
        """)
        self.character_selector.setMaximumWidth(200)

        self.emotion_selector = QComboBox(self)  # 情感选择框
        self.emotion_selector.setStyleSheet("""
            QComboBox {
                font-family: "Microsoft YaHei";
                font-size: 10pt;
                padding: 5px;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
        """)
        self.emotion_selector.setMaximumWidth(200)

        # 角色和情感选择的布局（水平布局）
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(5)  # 控件之间的间距
        selector_layout.setContentsMargins(0, 0, 0, 0)  # 布局四周的边距

        # 角色标签
        role_label = QLabel("角色：", self)
        role_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # 垂直居中，水平靠左
        role_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 固定大小，宽度和高度都不能改变
        role_label.setStyleSheet("margin: 0px; padding: 0px; font-family: 'Microsoft YaHei'; font-size: 10pt;")  # 外边距,标签内容与边框之间的内边距

        # 情感标签
        emotion_label = QLabel("情感：", self)
        emotion_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        emotion_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        emotion_label.setStyleSheet("margin: 0px; padding: 0px; font-family: 'Microsoft YaHei'; font-size: 10pt;")

        # 添加到布局
        selector_layout.addWidget(role_label)
        selector_layout.addWidget(self.character_selector)
        selector_layout.addWidget(emotion_label)
        selector_layout.addWidget(self.emotion_selector)

        # 消息输入框
        self.message_entry = QLineEdit(self)
        self.message_entry.setPlaceholderText("输入消息...")
        self.message_entry.setStyleSheet("""
            font-family: "Microsoft YaHei";
            font-size: 10pt;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
        """)
        self.message_entry.setFixedHeight(60)

        # 发送按钮
        self.send_button = QPushButton("发送", self)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 10pt;
                border-radius: 10px;
                padding: 10px 20px;
                width: 40px;
            }
            QPushButton:pressed {
                background-color: #45A049;
            }
        """)
        self.send_button.setFixedHeight(60)
        self.send_button.clicked.connect(self.send_message)  # 绑定点击事件

        # 语音按钮
        self.voice_button = QPushButton("语音输入", self)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 10pt;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:pressed {
                background-color: #45A049;
            }
        """)
        self.voice_button.setFixedHeight(60)
        self.voice_button.clicked.connect(self.toggle_voice_input)

        # 创建输入区域布局（包含输入框、发送按钮和语音按钮）
        self.entry_layout = QHBoxLayout()
        self.entry_layout.addWidget(self.message_entry)
        self.entry_layout.addWidget(self.send_button)
        self.entry_layout.addWidget(self.voice_button)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(selector_layout)  # 添加角色和情感选择行
        main_layout.addWidget(self.chat_area)   # 添加聊天显示区域
        main_layout.addLayout(self.entry_layout)  # 添加输入框和按钮

        self.setLayout(main_layout)

        # 绑定消息接收信号到显示函数
        self.message_received.connect(self.add_message_bubble)

    def resizeEvent(self, event):
        """窗口大小变化时调整气泡宽度"""
        super().resizeEvent(event)
        window_width = self.width()
        self.max_bubble_width = int(window_width * 0.7)  # 气泡最大宽度为窗口宽度的70%
        
        # 更新下拉框宽度为窗口宽度的30%
        combo_box_width = int(window_width * 0.3)
        self.character_selector.setMaximumWidth(combo_box_width)
        self.emotion_selector.setMaximumWidth(combo_box_width)

        # 更新所有现有气泡的宽度
        for i in range(self.chat_content.count()):
            item = self.chat_content.itemAt(i)
            if item and item.widget():
                bubble_container = item.widget()
                if isinstance(bubble_container, QFrame):
                    # 获取气泡容器中的布局
                    container_layout = bubble_container.layout()
                    if container_layout:
                        # 遍历布局中的所有项
                        for j in range(container_layout.count()):
                            widget = container_layout.itemAt(j).widget()
                            if isinstance(widget, QLabel):
                                # 更新气泡的最大宽度
                                widget.setMaximumWidth(self.max_bubble_width)
                                widget.adjustSize()

    def add_message_bubble(self, message, position="left"):
        """在聊天区域添加消息气泡"""
        # 创建气泡容器
        bubble_container = QFrame()
        bubble_container.setContentsMargins(0, 0, 0, 0)
        
        # 创建水平布局
        bubble_layout = QHBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(0)

        # 设置气泡样式
        bubble_color = "#E5E5E5" if position == "left" else "#4CAF50"
        text_color = "#000000" if position == "left" else "#FFFFFF"

        # 创建气泡标签
        bubble = QLabel(message)
        bubble.setWordWrap(True)  # 启用自动换行
        bubble.setMaximumWidth(self.max_bubble_width)  # 设置最大宽度
        bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {bubble_color};
                color: {text_color};
                font-family: "Microsoft YaHei";
                font-size: 12pt;
                padding: 10px 15px;
                border-radius: 10px;
                margin: 0px;
            }}
        """)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 允许选择文本

        # 根据位置添加气泡和弹性空间
        if position == "left":
            bubble_layout.addWidget(bubble, 0, Qt.AlignLeft)
            bubble_layout.addStretch(1)
        else:
            bubble_layout.addStretch(1)
            bubble_layout.addWidget(bubble, 0, Qt.AlignRight)

        # 添加到聊天内容区域
        self.chat_content.addWidget(bubble_container)
        
        # 滚动到底部
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动聊天区域到底部"""
        QApplication.processEvents()  # 确保布局更新
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )


    def request_character_and_emotion(self):
        """请求服务器返回角色和情感列表"""
        try:
            # 使用完全匹配服务器期望的格式
            init_message = "SYSTEM,COMMAND,LIST_CHARACTERS"  # 使用更明确的命令名称
            self.client_socket.send(init_message.encode('utf-8'))
            data = self.client_socket.recv(1024).decode('utf-8')

            try:
                # 解析JSON格式的角色和情感数据
                characters_and_emotions = json.loads(data)
                if isinstance(characters_and_emotions, dict):
                    self.character_selector.addItems(characters_and_emotions.keys())
                    
                    # 默认选择第一个角色，更新对应情感
                    if characters_and_emotions:
                        self.character_selector.setCurrentIndex(0)
                        self.update_emotions(characters_and_emotions)

                    # 角色变更时动态更新情感选项
                    self.character_selector.currentIndexChanged.connect(
                        lambda: self.update_emotions(characters_and_emotions)
                    )
                else:
                    logger.error(f"收到的数据格式不正确: {data}")
            except json.JSONDecodeError:
                logger.error(f"JSON解析失败，收到的数据: {data}")

        except Exception as e:
            logger.error(f"请求角色和情感数据时出错: {e}")


    def update_emotions(self, characters_and_emotions):
        """根据选中角色更新情感下拉框"""
        selected_character = self.character_selector.currentText()
        emotions = characters_and_emotions.get(selected_character, [])  # 获取选中角色的情感
        self.emotion_selector.clear()
        self.emotion_selector.addItems(emotions)  # 更新情感选项

    def toggle_voice_input(self):
        """切换语音输入状态"""
        if self.voice_thread is None or not self.voice_thread.isRunning():
            self.voice_button.setText("停止语音")
            self.voice_thread = VoiceInputThread()
            self.voice_thread.voice_input_signal.connect(self.handle_voice_input)
            self.voice_thread.start()
        else:
            self.voice_button.setText("语音输入")
            self.voice_thread.is_running = False
            self.voice_thread = None

    def handle_voice_input(self, text):
        """处理语音输入的文本"""
        if text:
            self.message_entry.setText(text)
            self.send_message()  # 自动发送语音识别的文本

    def send_message(self):
        """发送消息到服务器"""
        if not self.is_connected:  # 检查连接状态
            logger.warning("无法发送消息：连接已关闭")
            return

        message = self.message_entry.text().strip()
        if message:
            try:
                character = self.character_selector.currentText()
                emotion = self.emotion_selector.currentText()

                # 在聊天窗口显示消息
                self.add_message_bubble(f"{message}", "right")

                # 将消息发送给服务器
                formatted_message = f"{character},{emotion},{message}"
                self.client_socket.send(formatted_message.encode('utf-8'))

                self.message_entry.clear()
            except Exception as e:
                logger.error(f"发送消息时出错: {e}")
                self.is_connected = False  # 标记连接已断开

    def receive_message(self):
        """接收来自服务器的消息"""
        while self.is_connected:
            try:
                if not self.client_socket:
                    break

                # 首先接收消息长度
                data = bytearray()
                while self.is_connected:
                    chunk = self.client_socket.recv(4096)  # 使用更大的缓冲区
                    if not chunk:
                        break
                    data.extend(chunk)
                    
                    # 尝试解码已接收的数据
                    try:
                        message = data.decode('utf-8')
                        # 如果成功解码，清空缓冲区并处理消息
                        data.clear()
                        
                        if message.startswith('{') and message.endswith('}'):
                            # 这可能是角色和情感的JSON数据
                            try:
                                json_data = json.loads(message)
                                logger.info("收到角色和情感数据")
                            except json.JSONDecodeError:
                                self.message_received.emit(message)
                        else:
                            self.message_received.emit(message)
                        
                        break  # 成功处理一条完整消息后跳出内部循环
                    except UnicodeDecodeError:
                        # 如果解码失败，继续接收数据
                        continue

            except socket.error as e:
                if self.is_connected:  # 只在非正常关闭时记录错误
                    logger.error(f"接收消息错误: {e}")
                break
            except Exception as e:
                if self.is_connected:
                    logger.error(f"处理消息时发生错误: {e}")
                break

        self.connection_closed.emit()  # 发出连接关闭信号

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        try:
            # 首先标记连接状态为关闭
            self.is_connected = False
            
            # 停止语音线程
            if self.voice_thread and self.voice_thread.isRunning():
                self.voice_thread.is_running = False
                self.voice_thread.wait()

            # 如果socket还在连接状态，发送关闭消息
            if self.client_socket:
                try:
                    close_message = "SYSTEM,COMMAND,DISCONNECT"
                    self.client_socket.send(close_message.encode('utf-8'))
                    # 等待一小段时间确保消息发送完成
                    import time
                    time.sleep(0.1)
                except Exception as e:
                    logger.debug(f"发送关闭消息时出错: {e}")  # 使用debug级别，因为这是预期可能发生的
                finally:
                    try:
                        self.client_socket.shutdown(socket.SHUT_RDWR)  # 正确关闭socket
                    except Exception:
                        pass  # 忽略shutdown可能的错误
                    self.client_socket.close()
                    self.client_socket = None

        except Exception as e:
            logger.error(f"关闭窗口时出错: {e}")
        finally:
            event.accept()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec_())
