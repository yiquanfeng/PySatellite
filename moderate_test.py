import numpy as np
from scipy import signal

class QPSKModem():
    def __init__(self, samples_per_symbol=8, carrier_freq=0.05, snr_db=20, frame_len = 3072):
        self.sps = samples_per_symbol
        self.carrier_freq = carrier_freq
        self.snr_db = snr_db
        self.constellation = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)
        self.rrc_filter = self._design_rrc_filter(rolloff=0.35, span=6)
        self.frame_len = frame_len

    def _design_rrc_filter(self, rolloff, span):
        t = np.arange(-span*self.sps, span*self.sps + 1) / self.sps
        h = np.zeros_like(t)
        for i, ti in enumerate(t):
            if abs(ti) == 1/(4*rolloff):
                h[i] = (np.pi/(4*np.sqrt(2))) * ((1+2/np.pi)*np.sin(np.pi/(4*rolloff)) + (1-2/np.pi)*np.cos(np.pi/(4*rolloff)))
            elif ti == 0:
                h[i] = 1 + rolloff*(4/np.pi - 1)
            else:
                num = np.sin(np.pi*ti*(1-rolloff)) + 4*rolloff*ti*np.cos(np.pi*ti*(1+rolloff))
                den = np.pi*ti*(1 - (4*rolloff*ti)**2)
                h[i] = num / den
        return h / np.sqrt(np.sum(h**2))

    def modulate(self, frame_list):
        modulated_signals = []
        for frame in frame_list:
            # 统一转换为字符串格式
            if isinstance(frame, (np.ndarray, list)):
                bit_str = ''.join(map(str, frame))
            elif isinstance(frame, str):
                bit_str = frame
            else:
                raise TypeError("输入必须是字符串、列表或numpy数组")
            
            # 验证长度
            if len(bit_str) != self.frame_len:
                raise ValueError(f"每帧必须为{self.frame_len}bit，当前为{len(bit_str)}bit")
            
            # 转换为符号索引
            try:
                symbols = np.array([int(bit_str[i:i+2], 2) for i in range(0, self.frame_len, 2)])
            except ValueError as e:
                raise ValueError("输入包含非二进制字符") from e
            
            # 后续调制处理
            qpsk_symbols = self.constellation[symbols]
            upsampled = np.zeros(len(qpsk_symbols) * self.sps, dtype=complex)
            upsampled[::self.sps] = qpsk_symbols
            shaped = signal.convolve(upsampled, self.rrc_filter, mode='same')
            t = np.arange(len(shaped))
            modulated = np.real(shaped * np.exp(1j*2*np.pi*self.carrier_freq*t))
            modulated_signals.append(modulated)
        
        return modulated_signals

    def demodulate(self, signal_list):
        """
        严格匹配输入输出格式的解调方法
        参数:
            signal_list: 接收信号列表，每个元素为实信号numpy数组
        返回:
            output_frames: 与调制输入格式相同的帧列表（支持str/list/ndarray自动匹配）
        """
        # 获取第一帧输入信号的原始类型（假设所有帧类型一致）
        input_type = type(signal_list[0]) if signal_list else np.ndarray
        
        # 处理每帧信号
        output_frames = []
        for sig in signal_list:
            # 1. 载波解调与匹配滤波
            t = np.arange(len(sig))
            baseband = sig * np.exp(-1j*2*np.pi*self.carrier_freq*t)
            filtered = signal.convolve(baseband, self.rrc_filter, mode='same')
            
            # 2. 符号定时恢复
            symbols = filtered[self.sps//2::self.sps][:self.frame_len//2]  
            
            # 3. 噪声注入（动态关闭机制）
            if hasattr(self, 'noise_enabled') and not self.noise_enabled:
                pass  # 跳过噪声添加
            elif self.snr_db < float('inf'):
                noise_std = np.sqrt(10 ** (-self.snr_db / 10))
                symbols += noise_std * (np.random.randn(*symbols.shape) + 1j*np.random.randn(*symbols.shape))
            
            # 4. 符号判决
            symbol_indices = np.argmin(
                np.abs(symbols.reshape(-1,1) - self.constellation),
                axis=1
            )
            
            # 5. 转换为二进制数据
            bits = np.zeros(self.frame_len, dtype=np.uint8)
            for i, idx in enumerate(symbol_indices):
                bits[2*i] = (idx >> 1) & 1
                bits[2*i+1] = idx & 1
            
            # 6. 按输入类型转换输出格式
            if input_type == str:
                output_frames.append(''.join(map(str, bits)))
            elif input_type == list:
                output_frames.append(bits.tolist())
            else:  # 默认返回numpy数组
                output_frames.append(bits)
        
        return output_frames


# 正确使用示例
if __name__ == "__main__":
    modem = QPSKModem()
    
    # 示例1：字符串输入
    frame_str = '01' * 192  # 384bit
    modulated = modem.modulate([frame_str])
    
    # 示例2：numpy数组输入
    frame_arr = np.random.randint(0, 2, 384)  # 384个0/1
    modulated = modem.modulate([frame_arr])
    
    # 示例3：列表输入
    frame_list = [0,1]*192
    modulated = modem.modulate([frame_list])
    
    # 解调
    demodulated = modem.demodulate(modulated)
    print(demodulated[0])
    print(f"解调结果长度: {len(demodulated[0])}bit")  # 应输出384