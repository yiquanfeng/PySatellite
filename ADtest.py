import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import soundfile as sf
import librosa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy import signal

# def convert_to_binary_array(frames):
#     binary_list = []
#     for frame in frames:
#         for num in frame:
#             binary_str = '{:08b}'.format(int(num))
#             binary_digits = [int(digit) for digit in binary_str]
#             binary_list.extend(binary_digits)
#     return np.array(binary_list)

# def convert_from_binary_array(binary_array):
#     binary_str = ''.join(map(str, binary_array.astype(int)))
#     if len(binary_str) % 8 != 0:
#         raise ValueError("二进制数组的长度必须是8的倍数")
#     bytes_list = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
#     numbers = [int(byte, 2) for byte in bytes_list]
#     return np.array(numbers)

# def get_result(binary_signal):
#     quantized_signal = np.asarray(binary_signal).flatten()
#     quantized_signal = convert_from_binary_array(quantized_signal)
    
#     # 反量化
#     analog_signal = (quantized_signal / 255) * 2 - 1
    
#     # 关键修正：使用原始信号的时间轴进行插值
#     original_length = len(analog_signal)
#     original_time = np.linspace(0, 0.1, original_length, endpoint=False)
#     new_time = np.linspace(0, 0.1, 1280, endpoint=False)
    
#     # 线性插值
#     f = interp1d(original_time, analog_signal, kind='linear', bounds_error=False, fill_value=0)
#     reconstructed_signal = f(new_time)
    
#     return reconstructed_signal

# def load_audio_file(file_path):
#     audio_signal, sample_rate = sf.read(file_path)
#     # 如果是立体声，只取一个声道
#     if len(audio_signal.shape) > 1:
#         audio_signal = audio_signal[:, 0]
#     # 归一化到[-1, 1]范围
#     audio_signal = audio_signal / np.max(np.abs(audio_signal))
#     return audio_signal, sample_rate

# # 测试信号生成
# fs = 1280
# f = 100
# t_original = np.linspace(0, 0.1, fs, endpoint=False)
# original_signal = np.sin(2 * np.pi * f * t_original)

# # 量化
# quantized_signal = np.round((original_signal + 1) * 255 / 2).clip(0, 255).astype(np.uint8)

# # 分帧处理（保持您的分帧逻辑）
# frames = [quantized_signal[i:i+128] for i in range(0, len(quantized_signal), 128)]
# bin_frames = convert_to_binary_array(frames)
# bin_frames = bin_frames.reshape(10, 1024)




plt.rcParams["font.family"] = "SimHei"  # Windows 黑体的 PostScript 名称
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

fs = 88200 # 采样频率
bit_depth = 8  # 量化位深
frame_size = 128  # 二进制帧大小


class SoundOperation(object):
    def __init__(self):
        super.__init__()

    def sound_ADtrans(file_path, duration=1):
        original_signal, sample_rate, = librosa.load(file_path, sr=None, duration=duration)
        t_original = np.linspace(0, len(original_signal) / sample_rate, len(original_signal), endpoint=False)
        # 2. 采样
        sample_t = np.linspace(0, duration, int(fs*duration), endpoint=False)
        sampled_signal = np.interp(sample_t, t_original, original_signal)
        
        # 假设 sampled_signal 已通过插值得到，范围为 [-0.3, 0.3]
        min_val = np.min(sampled_signal)
        max_val = np.max(sampled_signal)

        # 处理边界情况（如全零信号）
        if max_val == min_val:
            max_val = min_val + 1e-6

        levels = 2 ** bit_depth
        step = (max_val - min_val) / levels  # 动态步长
        quantized_index = np.round((sampled_signal - min_val) / step)
        quantized_signal = np.clip(quantized_index, 0, levels - 1).astype(int)
        
        # 4. 转二进制帧
        frames = quantized_signal[:frame_size * 10].reshape(-1, frame_size)  # 取前10帧
        binary_frames = np.array([[int(b) for b in f"{num:08b}"] for frame in frames for num in frame])
        binary_frames = binary_frames.reshape(len(frames), -1)
        
        # 创建画布和三个子图，共享x轴
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        plt.subplots_adjust(hspace=0.4)  # 调整子图间距
        
        # 计算前3秒的样本数
        samples_per_second = sample_rate
        samples_in_3s = int(samples_per_second * 3)
        
        # 1. 原始信号子图
        axes[0].plot(t_original[:samples_in_3s], original_signal[:samples_in_3s])
        axes[0].set_title('1. 原始模拟信号')
        axes[0].grid(True, linestyle='--', alpha=0.7)
        
        # 2. 采样信号子图
        axes[1].plot(t_original[:samples_in_3s], original_signal[:samples_in_3s], '--', alpha=0.5)
        axes[1].stem(sample_t[:samples_in_3s], sampled_signal[:samples_in_3s], 'r', markerfmt='ro', basefmt=" ")
        axes[1].set_title(f'2. 采样信号 (fs={fs}Hz)')
        axes[1].grid(True, linestyle='--', alpha=0.7)
        
        # 3. 量化信号子图
        axes[2].stem(sample_t[:samples_in_3s], quantized_signal[:samples_in_3s], 'g', markerfmt='go', basefmt=" ")
        axes[2].set_title(f'3. {bit_depth}位量化信号')
        axes[2].grid(True, linestyle='--', alpha=0.7)
        axes[2].set_xlabel('时间 (秒)')  # 仅为底部子图设置x轴标签
        
        return fig, quantized_signal, binary_frames
    
    def sound_DAtrans(quantized_signal, sample_rate=44100, bit_depth=8, duration=3):
        """
        模拟数字-模拟转换过程
        
        参数:
            quantized_signal: 帧数据
            sample_rate: 采样率 (Hz)
            bit_depth: 量化位数
            duration: 信号持续时间 (秒)
        """
        # 1. 二进制数据转量化值
        # max_level = 2**bit_depth - 1
        # quantized_signal = np.array([
        #     int(''.join(map(str, frame)), 2)  # 二进制字符串转整数
        #     for frame in binary_frames
        # ]).astype(float)

        quantized_signal1 = np.asarray(quantized_signal).flatten()
        binary_str = ''.join(map(str, quantized_signal1.astype(int)))
        if len(binary_str) % 8 != 0:
            raise ValueError("二进制数组的长度必须是8的倍数")
        bytes_list = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
        numbers = [int(byte, 2) for byte in bytes_list]
        
        # 2. 归一化到[-1, 1]范围
        normalized_signal = 2 * (np.array(numbers) / 255) - 1
        
        # 3. 创建时间轴
        t_quantized = np.linspace(0, duration, len(normalized_signal), endpoint=False)
        
        # 4. 零阶保持重建 (阶梯状信号)
        t_reconstructed = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        reconstructed_signal = np.zeros_like(t_reconstructed)
        
        # 零阶保持插值
        step = len(t_reconstructed) / len(normalized_signal)
        for i in range(len(normalized_signal)):
            start_idx = int(i * step)
            end_idx = int((i + 1) * step)
            if end_idx > len(reconstructed_signal):
                end_idx = len(reconstructed_signal)
            reconstructed_signal[start_idx:end_idx] = normalized_signal[i]
        
        # 5. 低通滤波 (模拟重建滤波器)
        cutoff_freq = 0.45 * sample_rate  # 截止频率设为采样率的45%
        nyquist_freq = 0.5 * sample_rate
        normalized_cutoff = cutoff_freq / nyquist_freq
        
        # 设计8阶Butterworth低通滤波器
        b, a = signal.butter(8, normalized_cutoff, btype='low', analog=False)
        filtered_signal = signal.filtfilt(b, a, reconstructed_signal)
        
        # 6. 可视化DA转换过程
        fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
        plt.subplots_adjust(hspace=0.4)

        samples_per_second = sample_rate
        samples_in_3s = int(samples_per_second * 3)
        
        # # 1. 二进制数据
        # axes[0].imshow(binary_frames[:samples_in_3s], aspect='auto', cmap='binary')
        # axes[0].set_title('1. 二进制输入数据')
        # axes[0].set_ylabel('帧')
        
        # 2. 量化信号
        axes[0].stem(t_quantized[:samples_in_3s], normalized_signal[:samples_in_3s], 'g', markerfmt='go', basefmt=" ")
        axes[0].set_title(f'2. {bit_depth}位量化信号')
        axes[0].grid(True, linestyle='--', alpha=0.7)
        
        # 3. 重建信号 (零阶保持)
        axes[1].plot(t_reconstructed[:samples_in_3s], reconstructed_signal[:samples_in_3s], 'b-')
        axes[1].set_title('3. 重建信号 (零阶保持)')
        axes[1].grid(True, linestyle='--', alpha=0.7)
        
        # 4. 滤波后的模拟信号
        axes[2].plot(t_reconstructed[:samples_in_3s], filtered_signal[:samples_in_3s], 'r-')
        axes[2].set_title('4. 滤波后的模拟信号')
        axes[2].grid(True, linestyle='--', alpha=0.7)
        axes[2].set_xlabel('时间 (秒)')
        
        # plt.tight_layout()
        return fig, filtered_signal, t_reconstructed
    


# SoundOperation.sound_load("C:\\Users\\yiqua\\Music\\music_computer\\「僕は... .flac")