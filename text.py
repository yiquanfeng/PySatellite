import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


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
    
    def text_protocol(encoded_string:str) -> str:
        start_flag = "10101010"
        end_flag = "01010101"

        framed_data = start_flag + encoded_string + end_flag
        # print(framed_data)
        return framed_data
    
    def text_modulate(framed_data:str, samples_per_bit: int = 10):
        """可视化BPSK调制后的信号（带帧头帧尾）"""
        # BPSK调制：1→+1，0→-1
        signal = np.array([1 if bit == '1' else -1 for bit in framed_data])    
        # 上采样：每个比特扩展为多个样本
        upsampled_signal = np.repeat(signal, samples_per_bit) 
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
        return fig
    
    def text_channel