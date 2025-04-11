# bin/
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import expit  # sigmoid函数

# 设置参数
K = 4  # 约束长度
M = 2**(K-1)  # 状态数
block_length = 100  # 信息块长度
SNR_dB = 2  # 信噪比
iterations = 5  # 解码迭代次数

def encoder1(input_bits):
    """第一个卷积编码器 (通常用递归系统卷积码)"""
    # 这里简化实现，实际需要更复杂的移位寄存器
    output = []
    state = 0
    for bit in input_bits:
        output_bit = (bit + (state >> 1) + (state >> 2)) % 2  # 示例多项式
        output.append(output_bit)
        state = ((state << 1) | bit) % (1 << (K-1))
    return np.array(output)

def encoder2(input_bits):
    """第二个卷积编码器，使用交织后的输入"""
    # 类似第一个但多项式不同
    output = []
    state = 0
    for bit in input_bits:
        output_bit = (bit + (state >> 0) + (state >> 3)) % 2  # 不同多项式
        output.append(output_bit)
        state = ((state << 1) | bit) % (1 << (K-1))
    return np.array(output)

def interleaver(input_bits):
    """简单的随机交织器"""
    np.random.seed(0)  # 固定种子以便重现
    indices = np.random.permutation(len(input_bits))
    return input_bits[indices], indices

def deinterleaver(input_bits, indices):
    """解交织器"""
    inverse_indices = np.argsort(indices)
    return input_bits[inverse_indices]

def awgn_channel(coded_bits, snr_db):
    """添加高斯白噪声"""
    snr = 10**(snr_db / 10)
    noise_var = 1/(2*snr)  # 假设单位信号功率
    noise = np.sqrt(noise_var) * np.random.randn(len(coded_bits))
    received = 2*coded_bits - 1 + noise  # BPSK调制
    return received

def bcjr_decoder(received, encoder_func, prior=None):
    """简化的BCJR解码器"""
    if prior is None:
        prior = np.zeros_like(received)
    
    # 这里应该是完整的BCJR实现，简化起见用LLR近似
    llr = 2 * received / (0.5**2)  # 假设噪声方差0.5
    if encoder_func == encoder1:
        llr += 0.5 * prior  # 使用先验信息
    else:
        llr += 0.5 * prior
        
    decoded_bits = (llr > 0).astype(int)
    extrinsic = llr - prior - 2 * received  # 近似外部信息
    
    return decoded_bits, extrinsic

# 1. 生成随机信息位
info_bits = np.random.randint(0, 2, block_length)
print(info_bits)

# 2. 编码
encoded1 = encoder1(info_bits)  # 第一个编码器输出
interleaved_bits, interleave_indices = interleaver(info_bits)
encoded2 = encoder2(interleaved_bits)  # 第二个编码器输出

# 3. 组合编码输出（实际中会有打孔等操作）
coded_bits = np.concatenate([info_bits, encoded1, encoded2])

# 4. 通过噪声信道
received = awgn_channel(coded_bits, SNR_dB)

# 5. 分割接收信号
L = block_length
rx_info, rx_enc1, rx_enc2 = received[:L], received[L:2*L], received[2*L:]

# 6. Turbo解码
prior = np.zeros(L)  # 初始先验信息
for i in range(iterations):
    # 第一个解码器
    dec1, ext1 = bcjr_decoder(rx_info + rx_enc1, encoder1, prior)
    
    # 交织外部信息用于第二个解码器
    interleaved_ext, _ = interleaver(ext1)
    
    # 第二个解码器
    interleaved_rx_info, _ = interleaver(rx_info)
    dec2, ext2 = bcjr_decoder(interleaved_rx_info + rx_enc2, encoder2, interleaved_ext)
    
    # 解交织外部信息用于下一次迭代
    prior = deinterleaver(ext2, interleave_indices)
    
    # 计算当前解码结果
    final_llr = rx_info + 0.5*ext1 + 0.5*deinterleaver(ext2, interleave_indices)
    final_bits = (final_llr > 0).astype(int)
    
    print(final_bits)
    # 计算误码率
    errors = np.sum(final_bits != info_bits)
    print(f"迭代 {i+1}, 误码数: {errors}")

