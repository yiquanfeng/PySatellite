import numpy as np

class AmplitudeModem:
    def __init__(self, carrier_freq=1000, sample_rate=44100, bit_duration=0.1):
        """
        初始化调制解调器参数
        :param carrier_freq: 载波频率 (Hz)
        :param sample_rate: 采样率 (Hz)
        :param bit_duration: 每个比特的持续时间 (秒)
        """
        self.carrier_freq = carrier_freq
        self.sample_rate = sample_rate
        self.bit_duration = bit_duration
        self.samples_per_bit = int(sample_rate * bit_duration)
        
    def modulate(self, data):
        """
        幅度调制方法
        :param data: 二维列表，包含0和1的原始数据
        :return: 调制后的信号 (二维列表)
        """
        modulated_signals = []
        
        for row in data:
            # 验证输入数据
            if not all(bit in [0, 1] for bit in row):
                raise ValueError("输入数据必须只包含0和1")
                
            modulated_row = []
            t = np.linspace(0, self.bit_duration, self.samples_per_bit, endpoint=False)
            carrier = np.sin(2 * np.pi * self.carrier_freq * t)
            
            for bit in row:
                # 幅度调制：1对应高幅度(1.0)，0对应0幅度(0.0)
                amplitude = 1.0 if bit == 1 else 0.0
                modulated_bit = amplitude * carrier
                modulated_row.extend(modulated_bit.tolist())
                
            modulated_signals.append(modulated_row)
            
        return modulated_signals
    
    def demodulate(self, modulated_signals):
        demodulated_data = []
        t = np.linspace(0, self.bit_duration, self.samples_per_bit, endpoint=False)
        carrier = np.sin(2 * np.pi * self.carrier_freq * t)
        
        for signal_row in modulated_signals:
            # 将列表转为NumPy数组提高计算效率
            signal_array = np.array(signal_row)
            num_bits = len(signal_array) // self.samples_per_bit
            reshaped = signal_array.reshape((num_bits, self.samples_per_bit))
            
            # 向量化计算（比循环快得多）
            products = reshaped * carrier
            integrals = np.abs(products).sum(axis=1)
            bits = (integrals > 0.25 * self.samples_per_bit).astype(int)
            
            demodulated_data.append(bits.tolist())
        
        return demodulated_data


# 测试代码
if __name__ == "__main__":
    # 创建调制解调器实例
    modem = AmplitudeModem()
    
    # 测试数据
    test_data = [
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1]
    ]
    
    print("原始数据:")
    for row in test_data:
        print(row)
    
    # 调制
    modulated = modem.modulate(test_data)
    print("\n调制后的信号长度:", [len(row) for row in modulated])
    
    # 解调
    demodulated = modem.demodulate(modulated)
    print("\n解调后的数据:")
    for row in demodulated:
        print(row)
    
    # 验证是否一致
    print("\n数据是否一致:", test_data == demodulated)