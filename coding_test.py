import numpy as np
from scipy.special import logit, expit

class TurboEncoderDecoder:
    def __init__(self, frame_len=1024, constraint_length=3, interleaver_size=1024):
        """
        初始化Turbo编码器/解码器
        
        参数:
            constraint_length: int, 卷积码的约束长度
            interleaver_size: int, 交织器大小(应与输入数据长度匹配)
        """
        self.constraint_length = constraint_length
        self.interleaver_size = interleaver_size
        self.frame_len = frame_len
        
        # 生成随机交织器 (实际应用中应使用确定性的交织模式)
        np.random.seed(42)  # 固定种子以保证可重复性
        self.interleaver = np.random.permutation(interleaver_size)
        self.deinterleaver = np.argsort(self.interleaver)
        
        # 定义两个RSC(递归系统卷积)编码器的生成多项式
        # 这里使用经典的(7,5)Turbo码结构
        self.generator_matrix = np.array([[1, 0, 1],  # 反馈多项式 (1 + D^2)
                                         [1, 1, 1]]) # 前向多项式 (1 + D + D^2)
        
        # 初始化状态度量
        self.num_states = 2 ** (constraint_length - 1)
        
    def _rsc_encode(self, data, initial_state=0):
        """
        递归系统卷积(RSC)编码
        
        参数:
            data: 二进制输入序列
            initial_state: 初始状态
            
        返回:
            系统位和校验位的元组
        """
        state = initial_state
        systematic_bits = []
        parity_bits = []
        
        for bit in data:
            # 计算反馈
            feedback = (state & 0b1) ^ ((state >> 1) & 0b1)
            input_bit = int(bit) ^ feedback
            
            # 计算系统位和校验位
            systematic_bit = int(bit)
            parity_bit = input_bit ^ (state & 0b1) ^ ((state >> 1) & 0b1)
            
            systematic_bits.append(systematic_bit)
            parity_bits.append(parity_bit)
            
            # 更新状态
            state = ((input_bit << (self.constraint_length-2)) | (state >> 1))
        
        return np.array(systematic_bits), np.array(parity_bits)
    
    def encode(self, data):
        """
        Turbo编码
        
        参数:
            data: 二进制输入序列(1280位/帧)
            
        返回:
            编码后的比特流(系统位 + 第一校验位 + 第二校验位)
        """
        encoded_frames = []

        for frame in data:
            # 验证帧长度
            if len(frame) != self.frame_len:
                raise ValueError(f"输入帧必须为{self.frame_len}bit，当前为{len(frame)}bit")
            
            frame = np.array([int(bit) for bit in frame])
            
            # 第一个RSC编码器
            systematic1, parity1 = self._rsc_encode(frame)
            
            # 交织输入数据
            interleaved_data = frame[self.interleaver]
            
            # 第二个RSC编码器
            systematic2, parity2 = self._rsc_encode(interleaved_data)
            
            # 合并输出 (系统位 + 第一校验位 + 第二校验位)
            encoded = np.concatenate([systematic1, parity1, parity2])
            encoded_frames.append(encoded)
        
        return encoded_frames  
    
    def _log_map_decode(self, received, extrinsic_info):
        """
        简化的Log-MAP解码算法
        
        参数:
            received: 接收到的系统位和校验位
            extrinsic_info: 外部信息
            
        返回:
            解码后的LLR和更新的外部信息
        """
        # 这里使用简化的近似计算
        # 实际Log-MAP实现会更复杂
        
        num_bits = len(received) // 2
        systematic = received[:num_bits]
        parity = received[num_bits:]
        
        llr = np.zeros(num_bits)
        new_extrinsic = np.zeros(num_bits)
        
        for i in range(num_bits):
            # 简化计算 - 假设系统位和校验位受到相同噪声影响
            llr[i] = 2 * systematic[i] + extrinsic_info[i]
            new_extrinsic[i] = llr[i] - extrinsic_info[i] - 2 * systematic[i]
        
        return llr, new_extrinsic
    
    def decode(self, received_signal, iterations=6):
        """
        Turbo解码
        
        参数:
            received_signal: 接收到的信号(应为3840个浮点数)
            iterations: 迭代解码次数
            
        返回:
            解码后的二进制数据字符串
        """
        decoded_frames = []
        for frame in received_signal:
            if len(frame) != 3 * self.interleaver_size:
                raise ValueError("接收信号长度应为原始数据的3倍")
                
            # 分离接收到的系统位和校验位
            num_bits = self.interleaver_size
            received_sys = frame[:num_bits]
            received_parity1 = frame[num_bits:2*num_bits]
            received_parity2 = frame[2*num_bits:]
            
            # 初始外部信息
            extrinsic = np.zeros(num_bits)
            
            for _ in range(iterations):
                # 第一个解码器
                llr1, extrinsic1 = self._log_map_decode(
                    np.concatenate([received_sys, received_parity1]), 
                    extrinsic
                )
                
                # 交织外部信息
                interleaved_extrinsic = extrinsic1[self.interleaver]
                
                # 第二个解码器
                llr2, extrinsic2 = self._log_map_decode(
                    np.concatenate([received_sys[self.interleaver], received_parity2]), 
                    interleaved_extrinsic
                )
                
                # 解交织外部信息
                extrinsic = extrinsic2[self.deinterleaver]
            
            # 最终决策
            decoded = (llr1 > 0).astype(int)
            decoded_frames.append(decoded)

        return decoded_frames
    
# 示例用法
if __name__ == "__main__":
    # 创建Turbo编码器/解码器
    turbo = TurboEncoderDecoder(interleaver_size=128)
    
    # 生成随机测试数据
    np.random.seed(42)
    original_data = np.random.randint(0, 2, 128)
    print(len(original_data))
    original_data_str = ''.join(map(str, original_data))
    
    print("原始数据 (前20位):", original_data_str[:20])

    frames = [original_data]

    # 编码
    encoded = turbo.encode(frames)
    print("编码后一帧数据长度:", len(encoded[0]))
    
    # 模拟信道传输 (添加噪声)
    noise = np.random.normal(0, 0.5, len(encoded))  # AWGN噪声
    received = encoded + noise
    
    # 解码
    decoded = turbo.decode(received)  # 直接传递浮点数数组
    print("解码数据 (前20位):", decoded[:20])
    
    # 计算误码率
    errors = sum(1 for a, b in zip(original_data_str, decoded) if a != b)
    ber = errors / len(original_data_str)
    print(f"误码率(BER): {ber:.2%}")