import numpy as np
import matplotlib.pyplot as plt

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
fs = 1600
t_original = np.linspace(0, 0.1, fs, endpoint=False)
f = 100
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
sample_t = np.linspace(0, 0.1, 200, endpoint=False)
sample_signal = np.interp(sample_t, t_original, original_signal)


# 绘制采样后的信号
plt.subplot(3, 1, 2)
plt.stem(sample_t, sample_signal, label='Sampled Signal')
plt.title('Sampled Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()

## 量化
bit_depth = 16  
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

frames_tmp = [quantized_signal[i:i+16] for i in range(0, len(quantized_signal), 16)]

frames = [[hex(int(num)) for num in frame] for frame in frames_tmp]

for i, group in enumerate(frames[:5]):
    print(f"第 {i + 1} 组: {group}")

plt.subplot(3, 1, 3)
plt.stem(sample_t, quantized_signal, label='Quantized Signal')
plt.title('Quantized Signal')
plt.xlabel('Time (s)')
plt.ylabel('Quantized Value')
plt.legend()

plt.show()