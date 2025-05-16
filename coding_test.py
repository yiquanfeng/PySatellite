import numpy as np
from scipy.special import logit, expit

class TurboEncoderDecoder:
    def __init__(self, frame_len=1024, constraint_length=3, interleaver_size=1024):
        """
        初始化Turbo编码器/解码器
        
        参数:
            frame_len: int, 每帧的数据长度(比特数)
            constraint_length: int, 卷积码的约束长度(决定状态数)
            interleaver_size: int, 交织器大小(应与输入数据长度匹配)
        """
        self.constraint_length = constraint_length  # 卷积码约束长度
        self.interleaver_size = interleaver_size    # 交织器大小
        self.frame_len = frame_len                  # 每帧数据长度
        
        # 生成随机交织器 (实际应用中应使用确定性的交织模式)
        np.random.seed(42)  # 固定种子以保证可重复性
        self.interleaver = np.random.permutation(interleaver_size)  # 随机交织顺序
        self.deinterleaver = np.argsort(self.interleaver)  # 解交织顺序(交织的逆操作)
        
        # 定义两个RSC(递归系统卷积)编码器的生成多项式
        # 这里使用经典的(7,5)Turbo码结构
        # 生成矩阵定义编码器的反馈和前向连接
        self.generator_matrix = np.array([[1, 0, 1],  # 反馈多项式 (1 + D^2)
                                         [1, 1, 1]]) # 前向多项式 (1 + D + D^2)
        
        # 初始化状态度量
        self.num_states = 2 ** (constraint_length - 1)  # 计算编码器状态数
        
    def _rsc_encode(self, data, initial_state=0):
        """
        递归系统卷积(RSC)编码
        
        参数:
            data: 二进制输入序列(数组或列表)
            initial_state: 编码器初始状态(默认为0)
            
        返回:
            (systematic_bits, parity_bits): 系统位和校验位的元组
        """
        state = initial_state  # 初始化编码器状态
        systematic_bits = []   # 存储系统位
        parity_bits = []       # 存储校验位
        
        for bit in data:
            # 计算反馈项: 取状态的第0位和第1位进行异或
            feedback = (state & 0b1) ^ ((state >> 1) & 0b1)
            # 计算编码器输入: 输入比特与反馈异或
            input_bit = int(bit) ^ feedback
            
            # 计算系统位(直接输出输入比特)
            systematic_bit = int(bit)
            # 计算校验位: 输入比特与状态的第0位和第1位异或
            parity_bit = input_bit ^ (state & 0b1) ^ ((state >> 1) & 0b1)
            
            systematic_bits.append(systematic_bit)
            parity_bits.append(parity_bit)
            
            # 更新状态: 新输入移入高位，原状态右移
            state = ((input_bit << (self.constraint_length-2)) | (state >> 1))
        
        return np.array(systematic_bits), np.array(parity_bits)
    
    def encode(self, data):
        """
        Turbo编码(对多帧数据进行编码)
        
        参数:
            data: 二进制输入序列列表(每帧1280位)
            
        返回:
            encoded_frames: 编码后的比特流列表(每帧包含系统位 + 第一校验位 + 第二校验位)
        """
        encoded_frames = []  # 存储所有编码后的帧

        for frame in data:
            # 验证帧长度是否符合要求
            if len(frame) != self.frame_len:
                raise ValueError(f"输入帧必须为{self.frame_len}bit，当前为{len(frame)}bit")
            
            frame = np.array([int(bit) for bit in frame])  # 转换为整数数组
            
            # 第一个RSC编码器编码原始数据
            systematic1, parity1 = self._rsc_encode(frame)
            
            # 交织输入数据(按预定义的交织顺序重新排列)
            interleaved_data = frame[self.interleaver]
            
            # 第二个RSC编码器编码交织后的数据
            systematic2, parity2 = self._rsc_encode(interleaved_data)
            
            # 合并输出: 系统位 + 第一校验位 + 第二校验位
            encoded = np.concatenate([systematic1, parity1, parity2])
            encoded_frames.append(encoded)
        
        return encoded_frames  
    
    def _log_map_decode(self, received, extrinsic_info):
        """
        简化的Log-MAP解码算法(实际实现会更复杂)
        
        参数:
            received: 接收到的系统位和校验位(合并的数组)
            extrinsic_info: 来自另一个解码器的外部信息
            
        返回:
            (llr, new_extrinsic): 对数似然比和更新的外部信息
        """
        num_bits = len(received) // 2  # 计算原始数据长度
        systematic = received[:num_bits]  # 提取系统位
        parity = received[num_bits:]      # 提取校验位
        
        llr = np.zeros(num_bits)          # 初始化对数似然比数组
        new_extrinsic = np.zeros(num_bits)  # 初始化外部信息数组
        
        for i in range(num_bits):
            # 简化计算 - 假设系统位和校验位受到相同噪声影响
            # 实际Log-MAP算法会考虑网格图和前向/后向递归
            llr[i] = 2 * systematic[i] + extrinsic_info[i]
            new_extrinsic[i] = llr[i] - extrinsic_info[i] - 2 * systematic[i]
        
        return llr, new_extrinsic
    
    def decode(self, received_signal, iterations=6):
        """
        Turbo解码(迭代解码过程)
        
        参数:
            received_signal: 接收到的信号列表(每帧应为3840个浮点数)
            iterations: 迭代解码次数(默认为6次)
            
        返回:
            decoded_frames: 解码后的二进制数据列表
        """
        decoded_frames = []  # 存储所有解码后的帧
        data = np.array(received_signal)  # 转换为numpy数组
        
        for frame in data:
            # 验证接收信号长度是否符合要求
            if len(frame) != 3 * self.interleaver_size:
                raise ValueError("接收信号长度应为原始数据的3倍")
                
            # 分离接收到的系统位和两个校验位
            num_bits = self.interleaver_size
            received_sys = frame[:num_bits]           # 系统位
            received_parity1 = frame[num_bits:2*num_bits]  # 第一个校验位
            received_parity2 = frame[2*num_bits:]      # 第二个校验位
            
            # 初始外部信息(全零开始)
            extrinsic = np.zeros(num_bits)
            
            # 开始迭代解码
            for _ in range(iterations):
                # 第一个解码器解码(使用系统位和第一个校验位)
                llr1, extrinsic1 = self._log_map_decode(
                    np.concatenate([received_sys, received_parity1]), 
                    extrinsic
                )
                
                # 交织外部信息(为第二个解码器准备)
                interleaved_extrinsic = extrinsic1[self.interleaver]
                
                # 第二个解码器解码(使用交织后的系统位和第二个校验位)
                llr2, extrinsic2 = self._log_map_decode(
                    np.concatenate([received_sys[self.interleaver], received_parity2]), 
                    interleaved_extrinsic
                )
                
                # 解交织外部信息(为下一次迭代准备)
                extrinsic = extrinsic2[self.deinterleaver]
            
            # 最终决策: 根据LLR符号判断比特值(>0为1, <0为0)
            decoded = (llr1 > 0).astype(int)
            decoded_frames.append(decoded)

        return decoded_frames
    
# 示例用法
if __name__ == "__main__":
    # 创建Turbo编码器/解码器实例(使用较小的交织器大小便于测试)
    turbo = TurboEncoderDecoder(interleaver_size=128)
    
    # 生成随机测试数据(128位)
    np.random.seed(42)
    original_data = np.random.randint(0, 2, 128)
    original_data_str = ''.join(map(str, original_data))
    
    print("原始数据 (前20位):", original_data_str[:20])

    # 将数据放入列表中(可以处理多帧)
    frames = [original_data]

    # 编码
    encoded = turbo.encode(frames)
    print("编码后一帧数据长度:", len(encoded[0]), "(系统位+校验位1+校验位2)")
    
    # 模拟信道传输 (添加高斯白噪声)
    noise = np.random.normal(0, 0.5, len(encoded[0]))  # AWGN噪声
    received = [encoded[0] + noise]  # 添加噪声后的接收信号
    
    # 解码(使用6次迭代)
    decoded = turbo.decode(received, iterations=6)
    decoded_str = ''.join(map(str, decoded[0]))  # 转换为字符串
    
    # 计算误码率
    errors = sum(1 for a, b in zip(original_data_str, decoded_str) if a != b)
    ber = errors / len(original_data_str)
    print(f"误码率(BER): {ber:.2%}")