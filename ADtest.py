import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

import pyaudio
import wave
from mutagen.flac import FLAC
import pydub
import pydub.playback
import librosa

## music signal
music_path = "C:/Users/yiqua/Music/music_computer/「僕は... .flac"
audio = FLAC(music_path)
# pydub.playback.play(audio)

## measure the signal
# sample_rate = audio.info.sample_rate
# bit_depth = audio.info.bits_per_sample
# print("times(s) : ", audio.info.length)
# print("sample :", sample_rate)
# print("bits : ", bit_depth)
# audio_data, sample_rate = librosa.load(music_path)
# plt.figure(figsize=(20, 6))
# amplitude = np.abs(audio_data)

# plt.plot(np.arange(len(amplitude)) / sample_rate, amplitude, label='original music')
# print(len(np.arange(len(amplitude)) / sample_rate))
# plt.title('Waveform of the Audio')
# plt.xlabel('Time (s)')
# plt.ylabel('Amplitude')

# plt.show()
## -------- this is the demo ori ------- ##
fs = 1280
f = 100
t_original = np.linspace(0, 0.1, f, endpoint=False)
original_signal = np.sin(2 * np.pi * f * t_original)

plt.figure(figsize=(12, 9))
plt.subplot(3, 1, 1)
plt.plot(t_original, original_signal, label='Original Analog Signal')
plt.title('Original Analog Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()
## add the noise

## filter the wave

## catch the sample
T = 1 / fs
sample_t = np.linspace(0, 0.1, fs, endpoint=False)
sample_signal = np.interp(sample_t, t_original, original_signal)


# 绘制采样后的信号
plt.subplot(3, 1, 2)
plt.stem(sample_t, sample_signal, label='Sampled Signal')
plt.title('Sampled Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()

def convert_to_binary_array(frames):
    binary_list = []
    for frame in frames:
        for num in frame:
            # 将数字转换为 8 位二进制字符串
            binary_str = '{:08b}'.format(int(num))
            # 将二进制字符串拆分为单个字符并转换为整数
            binary_digits = [int(digit) for digit in binary_str]
            binary_list.extend(binary_digits)
    return np.array(binary_list)

## 量化
bit_depth = 8  
# 模拟信号的电压范围
voltage_range = [-1, 1]  
# 量化级别数量
quantization_levels = 2**bit_depth  
# 量化步长
step_size = (voltage_range[1] - voltage_range[0]) / quantization_levels  
# 量化操作
quantized_signal = np.round((sample_signal - voltage_range[0]) / step_size)
# 确保量化后的值在有效范围内
quantized_signal = np.clip(quantized_signal, 0, quantization_levels - 1)

frames = [quantized_signal[i:i+128] for i in range(0, 10)]

# frames = [[hex(int(num)) for num in frame] for frame in frames_tmp]
bin_frames = convert_to_binary_array(frames)
bin_frames = bin_frames.reshape(10, 1024)

for i, group in enumerate(bin_frames[:]):
    print(f"第 {i + 1} 组: {group}")

def get_frame():
    return bin_frames

plt.subplot(3, 1, 3)
plt.stem(sample_t, quantized_signal, label='Quantized Signal')
plt.title('Quantized Signal')
plt.xlabel('Time (s)')
plt.ylabel('Quantized Value')
plt.legend()
print(len(quantized_signal))
print(len(bin_frames))
plt.show()

# DA convert
time_points = np.linspace(0, 0.1 ,1280, endpoint=False)
f = interp1d(time_points, quantized_signal, kind="linear")

plt.figure(figsize=(12, 6))

# 绘制数字信号
plt.subplot(2, 1, 1)
plt.stem(time_points, quantized_signal, label='Digital Signal')
plt.title('Digital Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()

new_time_points = np.linspace(0, 0.1, 1280, endpoint=False)  
# 根据插值函数计算模拟信号的值
analog_signal = f(new_time_points)  

# 绘制模拟信号
# plt.subplot(2, 1, 2)
# plt.plot(new_time_points, analog_signal, label='Analog Signal', color='orange')
# plt.title('Analog Signal (After DA Conversion)')
# plt.xlabel('Time (s)')
# plt.ylabel('Amplitude')
# plt.legend()


# plt.show()

