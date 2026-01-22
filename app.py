import streamlit as st
import os
import subprocess
import threading
import time
import base64
from datetime import datetime

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
if 'show_calendar' not in st.session_state:
    st.session_state.show_calendar = False
if 'viewing_date' not in st.session_state:
    st.session_state.viewing_date = None

# 侧边栏配置
with st.sidebar:
 
    # 开始录音按钮
    if not st.session_state.recording:
        if st.button("开始录音", key="start_recording", type="primary"):
            # 生成时间戳用于文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 立即设置转录文件路径
            st.session_state.transcription_file = f'data/TXT/out_{timestamp}.txt'
            
            st.session_state.recording = True
            st.session_state.output_content = ""
            st.session_state.ai_response = ""
            st.session_state.selected_file = None
            st.session_state.selected_file_content = ""
            # 添加实时转录结果状态
            st.session_state.realtime_transcription = ""
            
            # 启动录音进程
            def run_recognition():
                # 运行main.py并获取进程对象，传递时间戳作为参数
                # 使用更兼容的方式捕获输出，避免capture_output参数在旧Python版本中不可用的问题
                process = subprocess.Popen(
                    ["python", "main.py", timestamp], 
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
 
    # 添加日历按钮
    if st.button("📅 日历", key="calendar_button"):
        st.session_state.show_calendar = True
        st.session_state.viewing_date = None
        st.rerun()
    
    st.divider()
    
    # 显示文件列表 - 使用expander实现折叠展开
    with st.expander("📝 语音识别文件", expanded=True):
        # 确保data/TXT文件夹存在
        if not os.path.exists('data/TXT'):
            os.makedirs('data/TXT', exist_ok=True)
        # 获取所有.txt文件
        out_files = [f for f in os.listdir('data/TXT') if f.endswith('.txt')]
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
        # 获取所有.wav文件
        audio_files = [f for f in os.listdir('data/WAV') if f.endswith('.wav')]
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
        # 获取所有.md文件
        cord_files = [f for f in os.listdir('data/MD') if f.endswith('.md')]
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

    
    # 实时转录结果显示
    st.subheader("📝 实时语音转录")
    

    # 读取并显示转录结果
    if st.session_state.transcription_file and os.path.exists(st.session_state.transcription_file):
        try:
            with open(st.session_state.transcription_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if content != st.session_state.realtime_transcription:
                st.session_state.realtime_transcription = content
                print(f"更新转录结果: {content}")
        except Exception as e:
            print(f"读取转录文件时出错: {e}")
    
    # 显示转录结果
    st.text_area("转录结果", value=st.session_state.realtime_transcription, height=300)
    
    # 添加自动刷新机制
    time.sleep(0.5)  # 短暂延迟，避免刷新过快
    st.rerun()
elif st.session_state.show_calendar:
    # 美化日历界面
    st.header("📅 日历")
    
    # 获取所有文件的日期和数量
    def get_file_stats():
        date_stats = {}
        # 检查TXT文件
        if os.path.exists('data/TXT'):
            for file in os.listdir('data/TXT'):
                if file.endswith('.txt'):
                    try:
                        parts = file.split('_')
                        for part in parts:
                            if len(part) == 8 and part.isdigit():
                                date_str = part
                                if date_str not in date_stats:
                                    date_stats[date_str] = 0
                                date_stats[date_str] += 1
                                break
                    except:
                        pass
        return date_stats
    
    file_stats = get_file_stats()
    
    # 生成月历
    import datetime
    
    # 获取当前日期或选中的月份
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.datetime.now()
    
    # 月份导航 - 美化样式
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← 上个月", key="prev_month", use_container_width=True):
            st.session_state.current_month = st.session_state.current_month.replace(day=1) - datetime.timedelta(days=1)
            st.rerun()
    with col2:
        st.subheader(f"{st.session_state.current_month.year}年{st.session_state.current_month.month}月")
    with col3:
        if st.button("下个月 →", key="next_month", use_container_width=True):
            # 计算下个月
            if st.session_state.current_month.month == 12:
                next_month = st.session_state.current_month.replace(year=st.session_state.current_month.year + 1, month=1, day=1)
            else:
                next_month = st.session_state.current_month.replace(month=st.session_state.current_month.month + 1, day=1)
            st.session_state.current_month = next_month
            st.rerun()
    
    # 生成月份的日历
    year = st.session_state.current_month.year
    month = st.session_state.current_month.month
    
    # 获取月份第一天是星期几 (0=周一, 6=周日)
    first_day = datetime.datetime(year, month, 1)
    first_day_weekday = first_day.weekday()  # 0=周一, 6=周日
    
    # 获取月份的天数
    if month == 12:
        last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
    days_in_month = last_day.day
    
    # 创建日历网格 - 美化样式
    st.write("")
    
    # 星期标题 - 美化样式
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    col_width = [1 for _ in range(7)]
    cols = st.columns(col_width)
    for i, day in enumerate(weekdays):
        cols[i].markdown(f"**{day}**", unsafe_allow_html=True)
    
    # 填充日历 - 美化样式
    day_num = 1
    week_num = 0
    
    while day_num <= days_in_month:
        cols = st.columns(col_width)
        
        # 填充第一周的空白
        if week_num == 0:
            for i in range(first_day_weekday):
                cols[i].write("")
        
        # 填充日期 - 美化样式
        start_col = first_day_weekday if week_num == 0 else 0
        for i in range(start_col, 7):
            if day_num > days_in_month:
                break
            
            # 构建日期字符串
            date_str = f"{year}{month:02d}{day_num:02d}"
            
            # 获取当天的txt文件数量
            file_count = file_stats.get(date_str, 0)
            
            # 日期按钮 - 美化样式
            button_label = f"{day_num}"
            if file_count > 0:
                button_label += f"({file_count}次)"
            
            # 美化按钮样式
            button_kwargs = {
                "key": f"cal_{date_str}",
                "use_container_width": True,
                "type": "primary" if file_count > 0 else "secondary"
            }
            
            if cols[i].button(button_label, **button_kwargs):
                # 直接在主界面显示对应日子的文件，不进入新页面
                st.session_state.viewing_date = date_str
                st.session_state.show_calendar = False  # 关闭日历视图
                st.rerun()
            
            day_num += 1
        week_num += 1
    
    # 返回按钮 - 美化样式
    if st.button("返回主界面", key="back_from_calendar", use_container_width=True):
        st.session_state.show_calendar = False
        st.session_state.viewing_date = None
        st.rerun()
        
elif st.session_state.viewing_date:
    # 显示特定日期的文件 - 美化样式
    viewing_date = st.session_state.viewing_date
    year = viewing_date[:4]
    month = viewing_date[4:6]
    day = viewing_date[6:8]
    
    # 美化标题
    st.header(f"📁 {year}年{month}月{day}日的文件")
    
    # 添加返回日历按钮
    if st.button("返回日历", key="back_to_calendar", type="secondary"):
        st.session_state.viewing_date = None
        st.session_state.show_calendar = True
        st.rerun()
    
    # 获取选中日期的文件
    def get_files_by_date(date_str):
        txt_files = []
        wav_files = []
        md_files = []
        
        # 检查TXT文件
        if os.path.exists('data/TXT'):
            for file in os.listdir('data/TXT'):
                if file.endswith('.txt') and date_str in file:
                    txt_files.append(file)
        
        # 检查WAV文件
        if os.path.exists('data/WAV'):
            for file in os.listdir('data/WAV'):
                if file.endswith('.wav') and date_str in file:
                    wav_files.append(file)
        
        # 检查MD文件
        if os.path.exists('data/MD'):
            for file in os.listdir('data/MD'):
                if file.endswith('.md') and date_str in file:
                    md_files.append(file)
        
        return txt_files, wav_files, md_files
    
    txt_files, wav_files, md_files = get_files_by_date(viewing_date)
    
    # 美化文件显示
    if txt_files or wav_files or md_files:
        # 使用卡片式布局
        if txt_files:
            st.subheader("📝 语音识别文件")
            for file in txt_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file}**")
                with col2:
                    if st.button("查看", key=f"view_txt_{file}", type="primary", use_container_width=True):
                        with open(f'data/TXT/{file}', 'r', encoding='utf-8') as f:
                            content = f.read()
                        st.session_state.selected_file = file
                        st.session_state.selected_file_content = content
                        st.session_state.viewing_date = None
                        st.rerun()
        
        if wav_files:
            st.subheader("🎵 音频文件")
            for file in wav_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file}**")
                with col2:
                    if st.button("查看", key=f"view_wav_{file}", type="primary", use_container_width=True):
                        with open(f'data/WAV/{file}', 'rb') as f:
                            audio_content = f.read()
                        st.session_state.selected_file = file
                        st.session_state.selected_file_content = audio_content
                        st.session_state.viewing_date = None
                        st.rerun()
        
        if md_files:
            st.subheader("🤖 AI总结文件")
            for file in md_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file}**")
                with col2:
                    if st.button("查看", key=f"view_md_{file}", type="primary", use_container_width=True):
                        with open(f'data/MD/{file}', 'r', encoding='utf-8') as f:
                            content = f.read()
                        st.session_state.selected_file = file
                        st.session_state.selected_file_content = content
                        st.session_state.viewing_date = None
                        st.rerun()
    else:
        # 美化空状态
        st.info("该日期暂无文件")
            
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
# 只在非录音状态且没有其他状态时显示主界面
if not st.session_state.recording and not st.session_state.show_calendar and not st.session_state.viewing_date and not st.session_state.selected_file:
    # 主界面
    st.header("🎤 语音识别与AI交互系统")
    st.info("请在侧边栏点击开始录音按钮开始使用")
    
    # 显示系统功能介绍
    st.markdown("""
    ### 系统功能
    - **语音识别**：将您的语音转换为文本
    - **AI 分析**：对识别的文本进行智能分析
    - **文件管理**：保存和管理所有录音和分析结果
    - **历史记录**：通过日历查看历史录音文件

    ### 使用流程
    1. 在侧边栏点击"开始录音"按钮
    2. 开始说话，系统会实时识别
    3. 点击"停止录音"按钮结束录音
    4. 系统自动进行AI分析
    5. 在侧边栏查看生成的文件
    6. 点击文件查看详细内容
    7. 使用"日历"功能按日期查看历史文件
    """)

