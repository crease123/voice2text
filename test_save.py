import os
from datetime import datetime

# 测试文件保存功能
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file_path = f'data/TXT/out_{timestamp}.txt'
audio_file_path = f'data/WAV/audio_{timestamp}.wav'
cord_file_path = f'data/MD/cord_{timestamp}.md'

print(f"测试文件路径:")
print(f"- 识别结果: {output_file_path}")
print(f"- 音频文件: {audio_file_path}")
print(f"- AI回复: {cord_file_path}")

# 确保文件夹存在
os.makedirs('data/TXT', exist_ok=True)
os.makedirs('data/WAV', exist_ok=True)
os.makedirs('data/MD', exist_ok=True)

# 测试创建识别结果文件
try:
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write("测试语音识别结果")
    print(f"✓ 成功创建识别结果文件: {output_file_path}")
    print(f"  文件大小: {os.path.getsize(output_file_path)} 字节")
except Exception as e:
    print(f"✗ 创建识别结果文件失败: {e}")

# 测试创建AI回复文件
try:
    with open(cord_file_path, 'w', encoding='utf-8') as f:
        f.write("# 测试AI回复\n\n这是一个测试回复")
    print(f"✓ 成功创建AI回复文件: {cord_file_path}")
    print(f"  文件大小: {os.path.getsize(cord_file_path)} 字节")
except Exception as e:
    print(f"✗ 创建AI回复文件失败: {e}")

# 测试创建空的WAV文件（仅用于测试路径）
try:
    import wave
    wf = wave.open(audio_file_path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(b'')
    wf.close()
    print(f"✓ 成功创建音频文件: {audio_file_path}")
    print(f"  文件大小: {os.path.getsize(audio_file_path)} 字节")
except Exception as e:
    print(f"✗ 创建音频文件失败: {e}")

# 测试读取文件
try:
    with open(output_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✓ 成功读取识别结果文件内容: {content}")
except Exception as e:
    print(f"✗ 读取识别结果文件失败: {e}")

print("\n测试完成!")