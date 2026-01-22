import os
import signal  # for keyboard events handling (press "Ctrl+C" to terminate recording)
import sys
import threading  # 用于创建线程监听回车键
import time  # 用于检查停止信号文件
from datetime import datetime  # 用于生成时间戳文件名

import dashscope
import pyaudio
from dashscope.audio.asr import *

mic = None
stream = None
output_file = None  # 输出文件对象
audio_file = None  # 音频文件对象
audio_frames = []  # 存储音频帧
recording_active = True  # 录音状态标志，用于控制主循环

# Set recording parameters
sample_rate = 16000  # sampling rate (Hz)
channels = 1  # mono channel
dtype = 'int16'  # data type
format_pcm = 'pcm'  # format of the audio data
block_size = 3200  # number of frames per buffer
# 生成时间戳
import sys
# 检查是否有命令行参数传递时间戳
if len(sys.argv) > 1:
    timestamp = sys.argv[1]
else:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
# 初始文件路径（临时使用）
temp_output_file_path = f'data/TXT/out_{timestamp}.txt'  # 临时输出文件路径
temp_cord_file_path = f'data/MD/cord_{timestamp}.md'  # 临时AI回复文件路径
temp_audio_file_path = f'data/WAV/audio_{timestamp}.wav'  # 临时音频文件路径
audio_file_path = temp_audio_file_path  # 音频文件路径

# 提前初始化音频捕获和缓冲区
p = pyaudio.PyAudio()
audio_stream = p.open(format=pyaudio.paInt16,
                      channels=channels,
                      rate=sample_rate,
                      input=True)
audio_buffer = []  # 用于缓冲WebSocket连接建立前的音频数据
websocket_connected = False  # WebSocket连接状态标记

# 缓冲音频数据的函数
def buffer_audio():
    global audio_buffer
    global websocket_connected
    print("开始缓冲音频数据...")
    while not websocket_connected:
        try:
            data = audio_stream.read(block_size, exception_on_overflow=False)
            audio_buffer.append(data)
        except Exception as e:
            print(f"缓冲音频时出错: {e}")
            break
    print(f"音频缓冲结束，已缓冲 {len(audio_buffer)} 帧数据")


# Real-time speech recognition callback
class Callback(RecognitionCallback):
    def on_open(self) -> None:
        global mic
        global stream
        global output_file
        global websocket_connected
        print('RecognitionCallback open.')
        # 标记WebSocket连接已建立
        websocket_connected = True
        mic = pyaudio.PyAudio()
        stream = mic.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=16000,
                          input=True)
        # 打开输出文件，准备写入识别结果
        output_file = open(temp_output_file_path, 'a', encoding='utf-8')
        print(f'已打开输出文件: {temp_output_file_path}')

    def on_close(self) -> None:
        global mic
        global stream
        global output_file
        print('RecognitionCallback close.')
        stream.stop_stream()
        stream.close()
        mic.terminate()
        stream = None
        mic = None
        # 关闭输出文件
        if output_file:
            output_file.close()
            output_file = None
            print(f'已关闭输出文件: {temp_output_file_path}')

    def on_complete(self) -> None:
        print('RecognitionCallback completed.')  # recognition completed

    def on_error(self, message) -> None:
        global recording_active
        print('RecognitionCallback task_id: ', message.request_id)
        print('RecognitionCallback error: ', message.message)
        # 设置录音状态为False，使主循环退出
        recording_active = False
        # Stop and close the audio stream if it is running
        if 'stream' in globals() and stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception as e:
                print(f"关闭音频流时出错: {e}")
        # 不再强制退出程序，让程序继续执行文件保存操作
        print("语音识别服务出错，将继续执行文件保存操作...")

    def on_event(self, result: RecognitionResult) -> None:
        global output_file
        sentence = result.get_sentence()
        if 'text' in sentence:
            text = sentence['text']
            print('RecognitionCallback text: ', text)
            # 只在句子结束时才写入文件，保存完整的句子
            if RecognitionResult.is_sentence_end(sentence):
                if output_file:
                    output_file.write(text + '\n')
                    output_file.flush()  # 立即刷新缓冲区，确保数据写入文件
                    print(f'已保存句子到文件: {text}')
                print(
                    'RecognitionCallback sentence end, request_id:%s, usage:%s'
                    % (result.get_request_id(), result.get_usage(sentence)))


def signal_handler(sig, frame):
    global recording_active
    print('Ctrl+C pressed, stop recognition ...')
    # 设置录音状态为False，使主循环退出
    recording_active = False
    # 停止识别服务
    if 'recognition' in globals():
        try:
            recognition.stop()
            print('Recognition stopped.')
            try:
                print(
                    '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
                    .format(
                        recognition.get_last_request_id(),
                        recognition.get_first_package_delay(),
                        recognition.get_last_package_delay(),
                    ))
            except Exception as e:
                print(f"获取识别 metrics 时出错: {e}")
        except Exception as e:
            print(f"停止识别服务时出错: {e}")
    # 不再退出程序，继续执行后续代码


def listen_for_enter():
    """监听回车键，用于停止录音"""
    global recording_active
    input()  # 等待用户按下回车键
    print('回车键被按下，停止录音...')
    recording_active = False  # 设置录音状态为False，使主循环退出



dashscope.api_key = 'sk-d5d59dea2ce2448a86158ac326977694'
dashscope.base_websocket_api_url='wss://dashscope.aliyuncs.com/api-ws/v1/inference'

# 创建识别回调对象，用于处理识别过程中的各种事件（如连接打开、关闭、错误、结果等）
callback = Callback()

# 创建识别服务实例，配置识别参数
# Call recognition service by async mode, you can customize recognition parameters, like model, format,
# sample_rate
recognition = Recognition(
    model='fun-asr-realtime',  # 指定使用的语音识别模型，fun-asr-realtime是阿里云的实时语音识别模型
    format=format_pcm,  # 设置音频数据格式为PCM格式
    # 'pcm'、'wav'、'opus'、'speex'、'aac'、'amr', you can check supported formats in document
    sample_rate=sample_rate,  # 设置音频采样率，16000Hz表示每秒采样16000次
    # support 8000, 16000
    semantic_punctuation_enabled=False,  # 是否启用语义标点符号功能，False表示不自动添加标点
    callback=callback)  # 设置回调函数对象，用于接收识别结果和状态更新

# 检查并删除可能存在的停止信号文件
if os.path.exists('stop_recording.txt'):
    print('发现残留的停止信号文件，删除它...')
    os.remove('stop_recording.txt')

# 启动音频缓冲线程
buffer_thread = threading.Thread(target=buffer_audio)
buffer_thread.daemon = True
buffer_thread.start()

# 启动语音识别服务，建立WebSocket连接
recognition.start()

# 注册信号处理器，用于捕获Ctrl+C中断信号
signal.signal(signal.SIGINT, signal_handler)
print("Press 'Enter' to stop recording and recognition...")  # 提示用户如何停止程序

# 启动回车键监听线程
enter_thread = threading.Thread(target=listen_for_enter)
enter_thread.daemon = True  # 设置为守护线程，主线程退出时自动结束
enter_thread.start()

# 立即开始收集音频数据，不等待WebSocket连接
print("开始主动收集音频数据...")

# 等待一段时间，让缓冲线程有时间收集音频数据
print("等待缓冲音频数据...")
time.sleep(0.5)

# 进入主循环，持续读取麦克风音频数据并发送给识别服务
# 首先添加缓冲的音频数据
if audio_buffer:
    print(f"添加 {len(audio_buffer)} 帧缓冲音频数据...")
    audio_frames.extend(audio_buffer)
    # 清空缓冲区
    audio_buffer = []
else:
    print("缓冲音频数据为空")
    # 手动从audio_stream读取一些数据作为初始数据
    try:
        data = audio_stream.read(block_size, exception_on_overflow=False)
        audio_frames.append(data)
        print(f"手动添加 1 帧初始音频数据")
    except Exception as e:
        print(f"添加初始音频数据时出错: {e}")

# 记录开始时间
start_time = time.time()
stop_signal_detected = False

print("进入主循环，开始持续收集音频数据...")

while recording_active:  # 使用recording_active标志控制循环
    # 检查是否存在停止信号文件
    if os.path.exists('stop_recording.txt'):
        if not stop_signal_detected:
            print('检测到停止信号，准备停止录音...')
            stop_signal_detected = True
            # 不要立即退出，再收集几帧数据确保完整性
            print("再收集几帧数据确保完整性...")
            for i in range(3):
                try:
                    data = audio_stream.read(block_size, exception_on_overflow=False)
                    audio_frames.append(data)
                    print(f"最后收集第 {i+1} 帧数据")
                except Exception as e:
                    print(f"最后收集数据时出错: {e}")
            # 删除停止信号文件
            os.remove('stop_recording.txt')
            # 退出循环
            recording_active = False
            break
    
    # 无论stream是否初始化，都收集音频数据
    try:
        # 优先使用提前初始化的audio_stream收集音频数据
        # 这样即使WebSocket连接失败，也能收集到音频数据
        data = audio_stream.read(block_size, exception_on_overflow=False)
        # 保存音频帧
        audio_frames.append(data)
        print(f"使用audio_stream收集数据，已收集 {len(audio_frames)} 帧")
        
        # 如果stream已初始化，也发送给识别服务
        if stream:
            # 将读取的音频数据帧发送给识别服务进行处理
            recognition.send_audio_frame(data)
            print("音频数据已发送给识别服务")
    except Exception as e:
        print(f"收集音频数据时出错: {e}")
        # 继续循环，不退出
        time.sleep(0.1)
    
    # 每收集几帧数据，就打印一次当前状态
    if len(audio_frames) % 5 == 0:
        print(f"当前状态: 已收集 {len(audio_frames)} 帧音频数据")
        print(f"录音持续时间: {time.time() - start_time:.2f} 秒")

print("录音已结束，继续执行后续代码...")  # 提示用户录音结束

# 保存音频文件
try:
    print(f"正在保存音频文件: {audio_file_path}")
    print(f"音频帧数: {len(audio_frames)}")
    # 确保data文件夹存在
    os.makedirs('data', exist_ok=True)
    # 保存为WAV文件
    import wave
    wf = wave.open(audio_file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # 16位=2字节
    wf.setframerate(sample_rate)
    if audio_frames:
        wf.writeframes(b''.join(audio_frames))
    else:
        # 即使没有音频数据，也创建一个空的WAV文件
        wf.writeframes(b'')
        print("没有音频数据，创建空的音频文件")
    wf.close()
    print(f"音频文件已保存: {audio_file_path}")
    print(f"音频文件大小: {os.path.getsize(audio_file_path)} 字节")
except Exception as e:
    print(f"保存音频文件时出错: {e}")
    # 即使出错，也尝试创建一个空的音频文件
    try:
        import wave
        wf = wave.open(audio_file_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b'')
        wf.close()
        print(f"已创建空的音频文件: {audio_file_path}")
    except Exception as e2:
        print(f"创建空音频文件时出错: {e2}")

# 停止语音识别服务，关闭WebSocket连接
try:
    # 检查recognition是否存在且未停止
    if 'recognition' in globals():
        recognition.stop()
        print("已停止语音识别服务")
except Exception as e:
    print(f"停止语音识别服务时出错: {e}")

# 关闭提前打开的音频流，避免资源泄漏
if 'audio_stream' in globals() and audio_stream:
    try:
        audio_stream.stop_stream()
        audio_stream.close()
        print("已关闭提前打开的音频流")
    except Exception as e:
        print(f"关闭音频流时出错: {e}")
if 'p' in globals() and p:
    try:
        p.terminate()
        print("已终止PyAudio对象")
    except Exception as e:
        print(f"终止PyAudio时出错: {e}")

# =====================================================================================================
try:
    from openai import OpenAI

    # 设置DeepSeek API
    api_key = "sk-c0e2db4baac34732b5fe022aca40961d"
    base_url = "https://api.deepseek.com"

    # 创建客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    # 读取文件内容
    try:
        with open(temp_output_file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        print(f"已读取识别结果文件: {temp_output_file_path}")
    except FileNotFoundError:
        print(f"识别结果文件不存在: {temp_output_file_path}")
        # 如果文件不存在，使用空字符串
        text = ""
    except Exception as e:
        print(f"读取识别结果文件时出错: {e}")
        # 如果读取失败，使用空字符串
        text = ""
    
    # 读取system.txt文件内容
    try:
        with open('system.txt', 'r', encoding='utf-8') as system_file:
            system_content = system_file.read()
        print("已读取system.txt文件")
    except FileNotFoundError:
        print("system.txt文件不存在，使用默认系统提示")
        system_content = "你是一个智能助手，帮助用户分析和处理输入的文本。"
    except Exception as e:
        print(f"读取system.txt文件时出错: {e}")
        system_content = "你是一个智能助手，帮助用户分析和处理输入的文本。"

    # 发送一个简单的问题
    try:
        if text:
            response = client.chat.completions.create(
                model="deepseek-chat",  # 使用deepseek-chat模型
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # 打印回复
            ai_response = response.choices[0].message.content
            print(ai_response)

            # 将AI回复保存到临时文件
            try:
                os.makedirs('data/MD', exist_ok=True)
                with open(temp_cord_file_path, 'w', encoding='utf-8') as cord_file:
                    cord_file.write(ai_response)
                print(f'AI回复已保存到临时文件: {temp_cord_file_path}')
            except Exception as e:
                print(f"保存AI回复文件时出错: {e}")
        else:
            print("没有识别到文本，跳过AI分析")
            # 即使没有识别到文本，也创建一个空的AI回复文件
            try:
                os.makedirs('data/MD', exist_ok=True)
                with open(temp_cord_file_path, 'w', encoding='utf-8') as cord_file:
                    cord_file.write("没有识别到文本内容")
                print(f'已创建空的AI回复文件: {temp_cord_file_path}')
            except Exception as e:
                print(f"创建空AI回复文件时出错: {e}")
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        # 即使API调用失败，也创建一个错误信息文件
        try:
            os.makedirs('data/MD', exist_ok=True)
            with open(temp_cord_file_path, 'w', encoding='utf-8') as cord_file:
                cord_file.write(f"API调用失败: {str(e)}")
            print(f'已创建API错误信息文件: {temp_cord_file_path}')
        except Exception as e:
            print(f"创建API错误信息文件时出错: {e}")
except Exception as e:
    print(f"导入OpenAI模块或初始化时出错: {e}")
    # 即使导入失败，也创建一个错误信息文件
    try:
        os.makedirs('data/MD', exist_ok=True)
        with open(temp_cord_file_path, 'w', encoding='utf-8') as cord_file:
            cord_file.write(f"模块导入失败: {str(e)}")
        print(f'已创建模块错误信息文件: {temp_cord_file_path}')
    except Exception as e:
        print(f"创建模块错误信息文件时出错: {e}")

# 重命名文件：根据内容生成文件名
try:
    # 检查是否识别到文本
    if text and len(text.strip()) > 0:
        print("\n开始根据文件内容生成文件名...")
        
        # 构建文件名生成提示
        filename_prompt = f"请分析以下文本内容，提取最能概括内容的简短关键词（1-3个词），用于作为文件名。\n\n文本内容：{text}\n\n要求：\n1. 关键词必须简洁明了\n2. 不要包含特殊字符\n3. 用中文回答\n4. 直接返回关键词，不要有其他说明"
        
        # 调用AI生成文件名关键词
        try:
            from openai import OpenAI
            
            # 设置DeepSeek API
            api_key = "sk-c0e2db4baac34732b5fe022aca40961d"
            base_url = "https://api.deepseek.com"
            
            # 创建客户端
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            filename_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个文件名生成助手，根据文本内容提取简洁的关键词作为文件名"},
                    {"role": "user", "content": filename_prompt}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            # 提取文件名关键词
            filename_keyword = filename_response.choices[0].message.content.strip()
            # 清理文件名，移除特殊字符
            filename_keyword = ''.join(c for c in filename_keyword if c.isalnum() or c == '_' or c == '-' or c == ' ')
            filename_keyword = filename_keyword.replace(' ', '_')
            filename_keyword = filename_keyword[:50]  # 限制长度
            
            print(f'生成的文件名关键词: {filename_keyword}')
            
            # 生成最终文件名
            final_output_filename = f'{filename_keyword}_{timestamp}.txt'
            final_output_path = f'data/TXT/{final_output_filename}'
            
            final_cord_filename = f'{filename_keyword}_{timestamp}.md'
            final_cord_path = f'data/MD/{final_cord_filename}'
            
            # 重命名文件
            if os.path.exists(temp_output_file_path):
                os.rename(temp_output_file_path, final_output_path)
                print(f'识别结果文件已重命名为: {final_output_path}')
            
            if os.path.exists(temp_cord_file_path):
                os.rename(temp_cord_file_path, final_cord_path)
                print(f'AI回复文件已重命名为: {final_cord_path}')
            
            # 重命名音频文件，使用和txt文件相同的文件名
            final_audio_filename = f'{filename_keyword}_{timestamp}.wav'
            final_audio_path = f'data/WAV/{final_audio_filename}'
            if os.path.exists(temp_audio_file_path):
                os.rename(temp_audio_file_path, final_audio_path)
                print(f'音频文件已重命名为: {final_audio_path}')
                
        except Exception as e:
            print(f"生成文件名时出错: {e}")
            print(f"使用默认文件名")
            
    else:
        print("没有识别到文本内容，使用默认文件名")
        
except Exception as e:
    print(f"文件重命名过程中出错: {e}")
    print(f"使用默认文件名")