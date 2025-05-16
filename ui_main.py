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

def plot_single_waveform(title, data):
    """绘制单个波形图，并返回 plt.Figure 对象（不显示窗口）"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 处理不同维度的数据
    data = downsample(data)  # 下采样
    
    if isinstance(data, (list, np.ndarray)):
        if len(np.array(data).shape) == 1:  # 一维数据
            ax.plot(data, label=title)
        elif len(np.array(data).shape) == 2:  # 二维数据
            for j, row in enumerate(data[:1]): 
                ax.plot(downsample(row), label=f'{title}[{j}]')
    
    ax.set_title(title)
    ax.set_xlabel('Sample Index')
    ax.set_ylabel('Amplitude')
    ax.grid(True)
    ax.legend(loc='upper right', fontsize='small')
    
    plt.tight_layout()
    return fig  # 返回 Figure 对象，不自动显示

def return_figures():
    try:
        # 存储所有 Figure 对象
        figures = []

        turbo = coding_test.TurboEncoderDecoder()
        _modulate = moderate_test.AmplitudeModem()
        _protocol = protocol.ProtocolHandler()

        fig_ad, quantized_signal, frames = ADtest.SoundOperation.sound_ADtrans("./BAK.wav")
        # print(f"frames:{len(frames[0])}")

        figures.append(fig_ad)

        # print("数据处理流程开始...")
        encode_bits = turbo.encode(frames)
        # print(f"ecode_bits_len:{len(encode_bits[0])}")

        send_p = _protocol.build_frames(encode_bits)
        # print(f"send_p_len:{len(send_p[0])}")

        _modulate_bits = _modulate.modulate(send_p)
        # print(f"modulate_bits_len:{len(_modulate_bits[0])}")

        demodulate_bits = _modulate.demodulate(_modulate_bits)
        # print(f"demodulate_bits_len:{len(demodulate_bits[0])}")

        recieve_p = _protocol.parse_frames(demodulate_bits)
        # print(f"recieve_p_len:{len(recieve_p[0])}")

        decode_bits = turbo.decode(recieve_p)
        # print(f"decode_bits_len:{len(decode_bits[0])}")

        fig_da, filtered_signal, t_reconstructed = ADtest.SoundOperation.sound_DAtrans(decode_bits)
        # print(f"da_bits:{len(filtered_signal)}")

        # print("数据处理流程完成")

        # 准备要绘制的数据
        data_to_plot = {
            'Encoded Bits': encode_bits,
            'Protocol Frames': send_p,
            'Modulated Signal': _modulate_bits,
            'Demodulated Signal': demodulate_bits,
            'Received Protocol': recieve_p,
            'Decoded Bits': decode_bits,
        }
        
        # print("开始绘制波形图...")
        for title, data in data_to_plot.items():
            fig = plot_single_waveform(title, data)  # 获取 Figure 对象
            figures.append(fig)  # 存储 Figure

        figures.append(fig_da)
        
    except MemoryError:
        print("错误: 内存不足，请减少数据量")
    except Exception as e:
        print(f"发生错误: {str(e)}")
    
    return figures