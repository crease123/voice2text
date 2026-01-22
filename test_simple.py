import subprocess
import time
import os

# 确保停止信号文件不存在
if os.path.exists('stop_recording.txt'):
    os.remove('stop_recording.txt')
    print("已删除残留的停止信号文件")

# 模拟app.py启动main.py的过程
print("启动main.py进程...")
process = subprocess.Popen(
    ["python", "main.py"], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE, 
    text=True
)
pid = process.pid
print(f"main.py进程PID: {pid}")

# 等待3秒，确保main.py完全启动
print("等待3秒，确保main.py完全启动...")
time.sleep(3)

# 等待5秒，模拟用户说话
print("等待5秒，模拟用户说话...")
time.sleep(5)

# 发送停止信号
print("发送停止信号...")
# 创建停止信号文件
with open('stop_recording.txt', 'w') as f:
    f.write('stop')

# 等待进程结束
print("等待main.py进程结束...")
stdout, stderr = process.communicate()

# 打印输出
print("=" * 80)
print("main.py 标准输出:")
print(stdout)
print("=" * 80)
print("main.py 标准错误:")
print(stderr)
print("=" * 80)

# 检查是否有新文件生成
print("检查是否有新文件生成...")
import glob
new_files = glob.glob('data/*')
print(f"当前data文件夹中的文件数量: {len(new_files)}")
print("最近的几个文件:")
for file in sorted(new_files, key=os.path.getmtime, reverse=True)[:5]:
    print(f"- {os.path.basename(file)} (修改时间: {os.path.getmtime(file)})")

# 检查最近生成的音频文件大小
print("\n检查最近生成的音频文件大小:")
audio_files = glob.glob('data/audio_*.wav')
if audio_files:
    latest_audio = sorted(audio_files, key=os.path.getmtime, reverse=True)[0]
    size = os.path.getsize(latest_audio)
    print(f"最近的音频文件: {os.path.basename(latest_audio)}")
    print(f"文件大小: {size} 字节")
    if size > 44:
        print("✓ 音频文件包含数据！")
    else:
        print("✗ 音频文件为空！")
else:
    print("没有找到音频文件！")

# 检查最近生成的识别结果文件
print("\n检查最近生成的识别结果文件:")
out_files = glob.glob('data/out_*.txt')
if out_files:
    latest_out = sorted(out_files, key=os.path.getmtime, reverse=True)[0]
    size = os.path.getsize(latest_out)
    print(f"最近的识别结果文件: {os.path.basename(latest_out)}")
    print(f"文件大小: {size} 字节")
    if size > 0:
        print("✓ 识别结果文件包含数据！")
        print("文件内容:")
        with open(latest_out, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("✗ 识别结果文件为空！")
else:
    print("没有找到识别结果文件！")