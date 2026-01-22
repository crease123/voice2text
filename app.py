import streamlit as st
import os
import subprocess
import threading
import time
import base64

# 设置页面配置
st.set_page_config(
    page_title="语音识别与AI交互系统",
    page_icon="🎤",
    layout="wide"
)

# 页面标题
# st.title("语音识别与AI交互系统")

# 创建状态变量
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'output_content' not in st.session_state:
    st.session_state.output_content = ""
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""
if 'system_prompt' not in st.session_state:
    # 读取system.txt内容
    if os.path.exists('system.txt'):
        with open('system.txt', 'r', encoding='utf-8') as f:
            st.session_state.system_prompt = f.read()
    else:
        st.session_state.system_prompt = "你是一个智能助手，帮助用户分析和处理输入的文本。"
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'selected_file_content' not in st.session_state:
    st.session_state.selected_file_content = ""

# 侧边栏配置
with st.sidebar:
 
    # 开始录音按钮
    if not st.session_state.recording:
        if st.button("开始录音", key="start_recording", type="primary"):
            st.session_state.recording = True
            st.session_state.output_content = ""
            st.session_state.ai_response = ""
            st.session_state.selected_file = None
            st.session_state.selected_file_content = ""
            
            # 启动录音进程
            def run_recognition():
                # 运行main.py并获取进程对象
                # 使用更兼容的方式捕获输出，避免capture_output参数在旧Python版本中不可用的问题
                process = subprocess.Popen(
                    ["python", "main.py"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                # 保存进程PID到会话状态
                st.session_state.main_pid = process.pid
                # 等待进程结束
                stdout, stderr = process.communicate()
                # 打印main.py的输出，便于调试
                print("=" * 80)
                print("main.py 标准输出:")
                print(stdout)
                print("=" * 80)
                print("main.py 标准错误:")
                print(stderr)
                print("=" * 80)
                # 将输出保存到会话状态，以便在界面上显示
                st.session_state.main_output = stdout
                st.session_state.main_error = stderr
                # 录音结束后更新状态
                st.session_state.recording = False
                # 清除PID
                if 'main_pid' in st.session_state:
                    del st.session_state.main_pid
                print("run_recognition 函数执行完成")
            
            # 在后台线程中运行
            thread = threading.Thread(target=run_recognition)
            thread.daemon = True
            thread.start()
            # 强制页面重新渲染，显示录音中状态
            st.rerun()
    else:
        st.warning("录音中...")
        # 显示录音状态
        st.info("录音进行中，正在识别语音...")
        
        # 添加停止录音按钮
        if st.button("停止录音", key="stop_recording"):
            # 使用信号发送停止命令
            if 'main_pid' in st.session_state and st.session_state.main_pid:
                import os
                import signal
                try:
                    # 发送SIGINT信号给main.py进程，与Ctrl+C效果相同
                    os.kill(st.session_state.main_pid, signal.SIGINT)
                    st.success("已发送停止录音信号，正在处理...")
                except Exception as e:
                    st.error(f"发送停止信号失败: {e}")
                    # 备用方案：创建停止信号文件
                    with open('stop_recording.txt', 'w') as f:
                        f.write('stop')
                    st.warning("已使用备用方案发送停止信号")
            else:
                # 备用方案：创建停止信号文件
                with open('stop_recording.txt', 'w') as f:
                    f.write('stop')
                st.warning("已使用备用方案发送停止信号")
            
            # 等待几秒钟让main.py处理停止信号
            import time
            # 增加等待时间，确保main.py有足够时间处理停止信号和保存文件
            time.sleep(3)
            
            # 检查main.py进程是否仍在运行
            if 'main_pid' in st.session_state and st.session_state.main_pid:
                import os
                import psutil
                try:
                    # 检查进程是否存在
                    process = psutil.Process(st.session_state.main_pid)
                    if process.is_running():
                        # 进程仍在运行，再次发送信号
                        os.kill(st.session_state.main_pid, signal.SIGINT)
                        st.warning("进程仍在运行，已再次发送停止信号")
                        # 再等待一段时间
                        time.sleep(2)
                except:
                    pass
            
            # 更新录音状态
            st.session_state.recording = False
            # 强制页面重新渲染，显示录音结束状态
            st.rerun()
    
 
    
    # 显示文件列表 - 使用expander实现折叠展开
    with st.expander("📝 语音识别文件", expanded=True):
        # 确保data/TXT文件夹存在
        if not os.path.exists('data/TXT'):
            os.makedirs('data/TXT', exist_ok=True)
        # 获取所有out_*.txt文件
        out_files = [f for f in os.listdir('data/TXT') if f.startswith('out_') and f.endswith('.txt')]
        # 按文件名排序（时间戳倒序）
        out_files.sort(reverse=True)
        
        if out_files:
            for file in out_files:
                if st.button(f"{file}", key=f"out_{file}"):
                    # 读取文件内容
                    with open(f'data/TXT/{file}', 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 更新状态
                    st.session_state.selected_file = file
                    st.session_state.selected_file_content = content
                    # 清空录音相关状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
        else:
            st.info("暂无语音识别文件")

    with st.expander("🎵 音频文件", expanded=True):
        # 确保data/WAV文件夹存在
        if not os.path.exists('data/WAV'):
            os.makedirs('data/WAV', exist_ok=True)
        # 获取所有audio_*.wav文件
        audio_files = [f for f in os.listdir('data/WAV') if f.startswith('audio_') and f.endswith('.wav')]
        # 按文件名排序（时间戳倒序）
        audio_files.sort(reverse=True)
        
        if audio_files:
            for file in audio_files:
                if st.button(f"{file}", key=f"audio_{file}"):
                    # 读取文件内容
                    with open(f'data/WAV/{file}', 'rb') as f:
                        audio_content = f.read()
                    # 更新状态
                    st.session_state.selected_file = file
                    st.session_state.selected_file_content = audio_content
                    # 清空录音相关状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
        else:
            st.info("暂无音频文件")

    with st.expander("🤖 AI总结文件", expanded=True):
        # 确保data/MD文件夹存在
        if not os.path.exists('data/MD'):
            os.makedirs('data/MD', exist_ok=True)
        # 获取所有cord_*.md文件
        cord_files = [f for f in os.listdir('data/MD') if f.startswith('cord_') and f.endswith('.md')]
        # 按文件名排序（时间戳倒序）
        cord_files.sort(reverse=True)
        
        if cord_files:
            for file in cord_files:
                if st.button(f"{file}", key=f"cord_{file}"):
                    # 读取文件内容
                    with open(f'data/MD/{file}', 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 更新状态
                    st.session_state.selected_file = file
                    st.session_state.selected_file_content = content
                    # 清空录音相关状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
        else:
            st.info("暂无AI回复文件")



# 主界面
if st.session_state.recording:
    # 录音状态界面
    st.header("🎤 录音中...")
    st.info("录音进行中，正在识别语音...")
    st.warning("请在侧边栏点击停止录音按钮结束录音")
    
    # 显示语音识别文件列表
    st.subheader("语音识别文件")
    # 确保data/TXT文件夹存在
    if not os.path.exists('data/TXT'):
        os.makedirs('data/TXT', exist_ok=True)
    # 获取所有out_*.txt文件
    out_files = [f for f in os.listdir('data/TXT') if f.startswith('out_') and f.endswith('.txt')]
    # 按文件名排序（时间戳倒序）
    out_files.sort(reverse=True)
    
    if out_files:
        for file in out_files[:5]:  # 只显示最近5个文件
            if st.button(f"📝 {file}", key=f"recording_out_{file}"):
                # 读取文件内容
                with open(f'data/TXT/{file}', 'r', encoding='utf-8') as f:
                    content = f.read()
                # 更新状态
                st.session_state.selected_file = file
                st.session_state.selected_file_content = content
                # 清空录音相关状态
                st.session_state.output_content = ""
                st.session_state.ai_response = ""
                # 强制页面重新渲染
                st.rerun()
    else:
        st.info("暂无语音识别文件")
elif st.session_state.selected_file:
    # 显示选中的文件内容
    st.header(f"📝 {st.session_state.selected_file}")
    
    # 根据文件类型显示内容
    if st.session_state.selected_file.endswith('.md'):
        st.markdown(st.session_state.selected_file_content)
        mime_type = "text/markdown"
    elif st.session_state.selected_file.endswith('.wav'):
        # 显示音频播放器
        st.audio(st.session_state.selected_file_content, format="audio/wav")
        mime_type = "audio/wav"
    else:
        st.text_area("文件内容", st.session_state.selected_file_content, height=400)
        mime_type = "text/plain"
    
    # 添加下载按钮
    st.download_button(
        label=f"下载 {st.session_state.selected_file}",
        data=st.session_state.selected_file_content,
        file_name=st.session_state.selected_file,
        mime=mime_type
    )
    
    # 添加返回按钮
    if st.button("返回主界面"):
        st.session_state.selected_file = None
        st.session_state.selected_file_content = ""
else:
    # 主界面
    st.header("🎤 语音识别与AI交互系统")
    st.info("请在侧边栏点击开始录音按钮开始使用")
    
    # 显示系统功能介绍
    st.markdown("""
    ### 系统功能
    - **语音识别**：将您的语音转换为文本
    - **AI 分析**：对识别的文本进行智能分析
    - **文件管理**：保存和管理所有录音和分析结果
    - **历史记录**：查看和下载历史录音文件
    
    ### 使用流程
    1. 在侧边栏点击"开始录音"按钮
    2. 开始说话，系统会实时识别
    3. 点击"停止录音"按钮结束录音
    4. 系统自动进行AI分析
    5. 在侧边栏查看生成的文件
    6. 点击文件查看详细内容
    """)

