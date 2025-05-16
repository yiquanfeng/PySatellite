import moderate_test, coding_test, ADtest, protocol
import numpy as np
import matplotlib.pyplot as plt

def downsample(data, max_samples=100):
    """下采样数据以避免内存问题"""
    if isinstance(data, (list, np.ndarray)):
        if len(data) > max_samples:
            step = len(data) // max_samples
            return data[::step]
    return data

def plot_waveforms(data_dict, rows, cols, frame_index=0):
    """绘制波形图的辅助函数
    frame_index: 要显示的frame索引(0-9)
    """
    plt.figure(figsize=(15, 10))
    
    for i, (title, data) in enumerate(data_dict.items(), 1):
        plt.subplot(rows, cols, i)
        
        # 处理不同维度的数据
        data = downsample(data)  # 下采样
        
        if isinstance(data, (list, np.ndarray)):
            if len(np.array(data).shape) == 1:  # 一维数据
                # 对于一维数据，我们只显示一部分
                start = frame_index * len(data) // 10
                end = (frame_index + 1) * len(data) // 10
                plt.plot(data[start:end], label=title)
            elif len(np.array(data).shape) == 2:  # 二维数据
                # 对于二维数据，我们只显示指定frame_index的行
                if frame_index < len(data):
                    plt.plot(downsample(data[frame_index]), label=f'{title}[{frame_index}]')
        
        plt.title(title)
        plt.xlabel('Sample Index')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.legend(loc='upper right', fontsize='small')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        turbo = coding_test.TurboEncoderDecoder()
        _modulate = moderate_test.AmplitudeModem()
        _protocol = protocol.ProtocolHandler()

        frames = ADtest.get_frame()
        
        print("数据处理流程开始...")
        encode_bits = turbo.encode(frames)
        send_p = _protocol.build_frames(encode_bits)
        _modulate_bits = _modulate.modulate(send_p)
        demodulate_bits = _modulate.demodulate(_modulate_bits)
        recieve_p = _protocol.parse_frames(demodulate_bits)
        decode_bits = turbo.decode(recieve_p)
        da_bits = ADtest.get_result(decode_bits)
        print("数据处理流程完成")

        # 准备要绘制的数据
        data_to_plot = {
            'Original Frames': frames,
            'Encoded Bits': encode_bits,
            'Protocol Frames': send_p,
            'Modulated Signal': _modulate_bits,
            'Demodulated Signal': demodulate_bits,
            'Received Protocol': recieve_p,
            'Decoded Bits': decode_bits,
            'Final Result': da_bits
        }

        # 计算需要的子图行数和列数
        num_plots = len(data_to_plot)
        rows = int(np.ceil(num_plots / 2))
        cols = 2 if num_plots > 1 else 1

        # 让用户选择要显示的frame
        frame_index = int(input("请输入要显示的frame索引(0-9): "))
        frame_index = max(0, min(9, frame_index))  # 确保在0-9范围内
        
        # 绘制波形图
        print(f"开始绘制波形图(显示frame {frame_index})...")
        plot_waveforms(data_to_plot, rows, cols, frame_index)
        
    except MemoryError:
        print("错误: 内存不足，请减少数据量")
    except Exception as e:
        print(f"发生错误: {str(e)}")