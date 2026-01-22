import subprocess
import time
import os

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

# 等待2秒，模拟用户说话
print("等待2秒，模拟用户说话...")
time.sleep(2)

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