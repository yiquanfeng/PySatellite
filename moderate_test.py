import numpy as np

class AmplitudeModem:
    def __init__(self, carrier_freq=1000, sample_rate=44100, bit_duration=0.1):
        """
        初始化调制解调器参数
        :param carrier_freq: 载波频率 (Hz)
        :param sample_rate: 采样率 (Hz)
        :param bit_duration: 每个比特的持续时间 (秒)
        """
        if carrier_freq <= 0:
            raise ValueError("载波频率必须为正数")
        if sample_rate <= 2 * carrier_freq:
            raise ValueError("采样率必须至少是载波频率的两倍(奈奎斯特准则)")
        if bit_duration <= 0:
            raise ValueError("比特持续时间必须为正数")
            
        self.carrier_freq = carrier_freq
        self.sample_rate = sample_rate
        self.bit_duration = bit_duration
        self.samples_per_bit = int(sample_rate * bit_duration)
        
        # 预计算载波信号
        t = np.linspace(0, self.bit_duration, self.samples_per_bit, endpoint=False)
        self.carrier = np.sin(2 * np.pi * self.carrier_freq * t)
        self.carrier_energy = np.sum(self.carrier ** 2)  # 用于归一化
        
    def modulate(self, data):
        """
        幅度调制方法
        :param data: 二维列表，包含0和1的原始数据
        :return: 调制后的信号 (二维列表)
        """
        if not isinstance(data, (list, np.ndarray)):
            raise ValueError("输入数据必须是列表或数组")
            
        modulated_signals = []
        
        for row in data:
            # 验证输入数据
            if not all(bit in [0, 1] for bit in row):
                raise ValueError("输入数据必须只包含0和1")
                
            modulated_row = []
            
            for bit in row:
                # 幅度调制：1对应高幅度(1.0)，0对应0幅度(0.0)
                amplitude = 1.0 if bit == 1 else 0.0
                modulated_bit = amplitude * self.carrier
                modulated_row.extend(modulated_bit.tolist())
                
            modulated_signals.append(modulated_row)
            
        return modulated_signals
    
    def demodulate(self, modulated_signals, threshold=0.5):
        """
        幅度解调方法
        :param modulated_signals: 调制后的信号 (二维列表)
        :param threshold: 解调阈值(0-1之间)
        :return: 解调后的数据 (二维列表)
        """
        if not isinstance(modulated_signals, (list, np.ndarray)):
            raise ValueError("输入信号必须是列表或数组")
        if not 0 <= threshold <= 1:
            raise ValueError("阈值必须在0和1之间")
            
        demodulated_data = []
        
        for signal_row in modulated_signals:
            # 将列表转为NumPy数组提高计算效率
            signal_array = np.array(signal_row)
            num_bits = len(signal_array) // self.samples_per_bit
            reshaped = signal_array.reshape((num_bits, self.samples_per_bit))
            
            # 使用相关检测(更鲁棒)
            products = reshaped * self.carrier
            correlations = np.sum(products, axis=1) / self.carrier_energy
            
            # 使用动态阈值
            bits = (correlations > threshold).astype(int)
            
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