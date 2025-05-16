import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import soundfile as sf

def convert_to_binary_array(frames):
    binary_list = []
    for frame in frames:
        for num in frame:
            binary_str = '{:08b}'.format(int(num))
            binary_digits = [int(digit) for digit in binary_str]
            binary_list.extend(binary_digits)
    return np.array(binary_list)

def convert_from_binary_array(binary_array):
    binary_str = ''.join(map(str, binary_array.astype(int)))
    if len(binary_str) % 8 != 0:
        raise ValueError("二进制数组的长度必须是8的倍数")
    bytes_list = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    numbers = [int(byte, 2) for byte in bytes_list]
    return np.array(numbers)

def get_frame():
    return bin_frames

def get_result(binary_signal):
    quantized_signal = np.asarray(binary_signal).flatten()
    quantized_signal = convert_from_binary_array(quantized_signal)
    
    # 反量化
    analog_signal = (quantized_signal / 255) * 2 - 1
    
    # 关键修正：使用原始信号的时间轴进行插值
    original_length = len(analog_signal)
    original_time = np.linspace(0, 0.1, original_length, endpoint=False)
    new_time = np.linspace(0, 0.1, 1280, endpoint=False)
    
    # 线性插值
    f = interp1d(original_time, analog_signal, kind='linear', bounds_error=False, fill_value=0)
    reconstructed_signal = f(new_time)
    
    return reconstructed_signal

def load_audio_file(file_path):
    audio_signal, sample_rate = sf.read(file_path)
    # 如果是立体声，只取一个声道
    if len(audio_signal.shape) > 1:
        audio_signal = audio_signal[:, 0]
    # 归一化到[-1, 1]范围
    audio_signal = audio_signal / np.max(np.abs(audio_signal))
    return audio_signal, sample_rate

# 测试信号生成
fs = 1280
f = 100
t_original = np.linspace(0, 0.1, fs, endpoint=False)
original_signal = np.sin(2 * np.pi * f * t_original)

# 量化
quantized_signal = np.round((original_signal + 1) * 255 / 2).clip(0, 255).astype(np.uint8)

# 分帧处理（保持您的分帧逻辑）
frames = [quantized_signal[i:i+128] for i in range(0, len(quantized_signal), 128)]
bin_frames = convert_to_binary_array(frames)
bin_frames = bin_frames.reshape(10, 1024)
