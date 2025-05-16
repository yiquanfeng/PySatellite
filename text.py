import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy import signal


class TextOperation(object):
    def __init__():
        super.__init__()

# encode to 8bit binary
    def text_encode(string):
        binary_list = []
        for char in string:
            # 获取字符的Unicode码点
            code_point = ord(char)
            # 将码点转换为二进制字符串，并去掉前缀 '0b'
            binary_str = bin(code_point)[2:]
            # 左侧补0，使字符串达到8位长度
            padded_binary = binary_str.zfill(8)
            binary_list.append(padded_binary)
            binary_final = "".join(binary_list)
            # print(binary_final)
        return binary_final
    
    def text_decode(binary_final:str):
        bytes_list = [binary_final[i:i+8] for i in range(0, len(binary_final), 8)]
        decoded_chars = []
        for byte in bytes_list:
            code_point = int(byte, 2)
            char = chr(code_point)
            decoded_chars.append(char)
        return ''.join(decoded_chars)
    
    def text_protocol(encoded_string:str) -> str:
        start_flag = "10101010"
        end_flag = "01010101"

        framed_data = start_flag + encoded_string + end_flag
        # print(framed_data)
        return framed_data
    
    def text_deprotocol(framed_data:str):
        return framed_data[8:-8]
    
    def text_modulate(framed_data:str, samples_perbit: int = 10):
        """可视化BPSK调制后的信号（带帧头帧尾）"""
        # BPSK调制：1→+1，0→-1
        signal = np.array([1 if bit == '1' else -1 for bit in framed_data])    
        # 上采样：每个比特扩展为多个样本
        upsampled_signal = np.repeat(signal, samples_perbit) 
        # 创建时间轴
        t = np.arange(len(upsampled_signal))
        # 绘制波形图
        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_subplot(111)
        # 绘制波形图
        ax.plot(t, upsampled_signal, 'b-', linewidth=1.5)  
        # 添加网格和标记
        ax.grid(True, alpha=0.3)
        ax.set_title('BPSK调制后的信号（带帧头帧尾）')
        ax.set_xlabel('样本')
        ax.set_ylabel('幅度')
        return fig, upsampled_signal
    
    def text_demodulate(received_signal: np.ndarray, samples_perbit: int = 10) -> str:
        """
        解调经过BPSK调制并通过信道传输的信号
        """
        # 计算比特数
        num_bits = len(received_signal) // samples_perbit
        
        # 初始化解调后的比特列表
        demodulated_bits = []
        
        # 对每个比特周期进行处理
        for i in range(num_bits):
            # 提取当前比特周期内的样本
            start_idx = i * samples_perbit
            end_idx = (i + 1) * samples_perbit
            bit_samples = received_signal[start_idx:end_idx]
            
            # 计算当前比特周期内的平均幅度
            avg_amplitude = np.mean(bit_samples)
            
            # 根据平均幅度判断比特值（大于0为1，小于等于0为0）
            demodulated_bits.append('1' if avg_amplitude > 0 else '0')
        
        # 转换为字符串
        demodulated_data = ''.join(demodulated_bits)
        
        # 绘制解调后的比特判决结果
        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_subplot(111)
        
        # 创建解调后信号的可视化（上采样以便于观察）
        demodulated_signal = np.array([1 if bit == '1' else -1 for bit in demodulated_data])
        upsampled_demodulated = np.repeat(demodulated_signal, samples_perbit)
        t_demod = np.arange(len(upsampled_demodulated))
        
        ax.plot(t_demod, upsampled_demodulated, 'r-', linewidth=1.5, label='解调判决')
        ax.grid(True, alpha=0.3)
        ax.set_title('解调后的比特判决')
        ax.set_xlabel('样本')
        ax.set_ylabel('判决幅度')
        ax.legend()
        
        return fig, demodulated_data
    
    def text_channel(signal: np.ndarray):
        attenuation = float(0.5)
        snr_db = float(10.0)

        attenuated_signal = signal * attenuation
        # 计算噪声功率
        signal_power = np.mean(attenuated_signal ** 2)
        snr_linear = 10 ** (snr_db / 10)
        noise_power = signal_power / snr_linear
        noise = np.random.normal(0, np.sqrt(noise_power), len(attenuated_signal))

        received_signal = attenuated_signal + noise
        t = np.arange(len(received_signal))
        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_subplot(111)
        # 绘制波形图
        ax.plot(t, received_signal, 'b-', linewidth=1.5)  
        # 添加网格和标记
        ax.grid(True, alpha=0.3)
        ax.set_title('经过信道后的信号')
        ax.set_xlabel('样本')
        ax.set_ylabel('幅度')

        return fig, received_signal