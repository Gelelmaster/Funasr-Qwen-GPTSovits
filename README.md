这是一个集合了 FunASR 语音识别输入，调用大模型 Qwen-turbo-Turbo LLM ，再通过 GPTSovits 进行语音输出（可选择角色）的本地大模型程序。

## 环境要求：
1. python >= 3.9.0  ，建议在 conda 虚拟环境下运行
``` sh
conda create -n FunLocalGPT python=3.9
conda activate FunLocalGPT
```

##### 最好有cuda，不然推理很慢，我的环境是RTX4060 laptop, 不知道什么原因，只有在 torch 和 torchaudio 是2.4.1版本时推理速度才正常，更新到2.5.0版本时推理很慢。
所以这里建议装固定版本  
Torch version: 2.4.1+cu121  
Torchvision version: 0.19.1+cu121  
Torchaudio version: 2.4.1+cu121  

2. 查看 cuda 版本
``` sh
nvcc --version
```

3. 安装对应的 ```torch torchvision torchaudio```
``` sh
pip install torch==2.4.1+cu121 torchvision==0.19.1+cu121 torchaudio==2.4.1+cu121 --extra-index-url https://download.pytorch.org/whl/cu121
```
  
## 文件下载
### FunASR
4. 该模型需要 modelscope
``` sh
pip install modelscope
```
5. 需要 [SenseVoiceSmall](https://huggingface.co/FunAudioLLM/SenseVoiceSmall/tree/main)
``` sh
git clone https://huggingface.co/FunAudioLLM/SenseVoiceSmall
```
6. 需要 VAD文件，这里使用 [speech_fsmn_vad_zh-cn-16k-common-pytorch](https://modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/files)
``` sh
git clone https://www.modelscope.cn/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch.git
```

### Qwen LLM
7. 根据对应模型这里是 [Qwen-turbo-Turbo-2024-09-19](https://bailian.console.aliyun.com/?spm=5176.29619931.J__Z58Z6CX7MY__Ll8p1ZOR.1.4a3b59fcy2QO90#/model-market/detail/qwen-turbo-0919?tabKey=sdk) 的官方文档获取 API-KEY，然后在系统环境变量里配置
``` sh
DASHSCOPE_API_KEY = 我的 API-KEY
```  
当然也可以选择其它模型进行调用，之后我计划采用本地大模型进行微调，看情况~ 

### GPTSovits
8. 采用 [X-T-E-R](https://github.com/X-T-E-R/GPT-SoVITS-Inference) 的 GPTSovits 修改版本
``` sh
git clone https://github.com/X-T-E-R/GPT-SoVITS-Inference.git
```
需要先创建语音模型，直接双击bat文件运行打开网页，在网页界面创建模型，再运行程序。  
或者在本地新建一个存放模型的文件夹 trained，将下载到的模型放到该目录下，运行程序。  
  
9. 拷贝程序文件到本地
``` sh
git clone https://github.com/Gelelmaster/Funasr-Qwen-GPTSovits.git
```
10. 最后安装依赖，``` requirements.txt 不完整，根据提示安装对应依赖。```
``` sh
pip install -r requirement.txt
```
