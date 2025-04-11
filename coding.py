import numpy as np
import matplotlib.pyplot as plt
from scipy.special import expit
from PySide2.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                              QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                              QTextEdit, QTabWidget, QGroupBox)
from PySide2.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class TurboCodeSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Turbo码仿真系统")
        self.setGeometry(100, 100, 1000, 800)
        
        self.init_ui()
        self.init_parameters()
        
    def init_parameters(self):
        # 默认参数
        self.K = 4  # 约束长度
        self.block_length = 1024  # 信息块长度
        self.SNR_dB = 2.0  # 信噪比
        self.iterations = 5  # 解码迭代次数
        self.generator_poly1 = 0o15  # 第一个编码器的生成多项式(八进制)
        self.generator_poly2 = 0o13  # 第二个编码器的生成多项式(八进制)
        
    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 参数设置区域
        param_group = QGroupBox("仿真参数")
        param_layout = QVBoxLayout()
        
        # 约束长度
        self.k_spin = QSpinBox()
        self.k_spin.setRange(3, 8)
        self.k_spin.setValue(4)
        param_layout.addWidget(QLabel("约束长度(K):"))
        param_layout.addWidget(self.k_spin)
        
        # 块长度
        self.block_spin = QSpinBox()
        self.block_spin.setRange(100, 10000)
        self.block_spin.setValue(1024)
        param_layout.addWidget(QLabel("信息块长度:"))
        param_layout.addWidget(self.block_spin)
        
        # 信噪比
        self.snr_spin = QDoubleSpinBox()
        self.snr_spin.setRange(-10, 20)
        self.snr_spin.setValue(2.0)
        param_layout.addWidget(QLabel("SNR(dB):"))
        param_layout.addWidget(self.snr_spin)
        
        # 迭代次数
        self.iter_spin = QSpinBox()
        self.iter_spin.setRange(1, 20)
        self.iter_spin.setValue(5)
        param_layout.addWidget(QLabel("解码迭代次数:"))
        param_layout.addWidget(self.iter_spin)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # 控制按钮
        self.run_btn = QPushButton("运行仿真")
        self.run_btn.clicked.connect(self.run_simulation)
        layout.addWidget(self.run_btn)
        
        # 结果显示区域
        self.tabs = QTabWidget()
        
        # 结果文本标签
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.tabs.addTab(self.result_text, "文本结果")
        
        # 图形结果标签
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.tabs.addTab(self.canvas, "图形结果")
        
        layout.addWidget(self.tabs)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    
    def run_simulation(self):
        # 更新参数
        self.K = self.k_spin.value()
        self.block_length = self.block_spin.value()
        self.SNR_dB = self.snr_spin.value()
        self.iterations = self.iter_spin.value()
        
        # 运行仿真
        info_bits, decoded_bits, ber_history = self.simulate_turbo_code()
        
        # 显示结果
        self.show_results(info_bits, decoded_bits, ber_history)
        
    def simulate_turbo_code(self):
        # 1. 生成随机信息位
        info_bits = np.random.randint(0, 2, self.block_length)
        
        # 2. 编码
        encoded1 = self.encoder1(info_bits)  # 第一个编码器输出
        interleaved_bits, interleave_indices = self.interleaver(info_bits)
        encoded2 = self.encoder2(interleaved_bits)  # 第二个编码器输出
        
        # 3. 组合编码输出（实际中会有打孔等操作）
        coded_bits = np.concatenate([info_bits, encoded1, encoded2])
        
        # 4. 通过噪声信道
        received = self.awgn_channel(coded_bits, self.SNR_dB)
        
        # 5. 分割接收信号
        L = self.block_length
        rx_info, rx_enc1, rx_enc2 = received[:L], received[L:2*L], received[2*L:]
        
        # 6. Turbo解码
        prior = np.zeros(L)  # 初始先验信息
        ber_history = []
        
        for i in range(self.iterations):
            # 第一个解码器
            dec1, ext1 = self.bcjr_decoder(rx_info + rx_enc1, self.encoder1, prior)
            
            # 交织外部信息用于第二个解码器
            interleaved_ext, _ = self.interleaver(ext1)
            
            # 第二个解码器
            interleaved_rx_info, _ = self.interleaver(rx_info)
            dec2, ext2 = self.bcjr_decoder(interleaved_rx_info + rx_enc2, self.encoder2, interleaved_ext)
            
            # 解交织外部信息用于下一次迭代
            prior = self.deinterleaver(ext2, interleave_indices)
            
            # 计算当前解码结果
            final_llr = rx_info + 0.5*ext1 + 0.5*self.deinterleaver(ext2, interleave_indices)
            final_bits = (final_llr > 0).astype(int)
            
            # 计算误码率
            errors = np.sum(final_bits != info_bits)
            ber = errors / self.block_length
            ber_history.append(ber)
            
        return info_bits, final_bits, ber_history
    
    def encoder1(self, input_bits):
        """第一个卷积编码器 (递归系统卷积码)"""
        # 多项式: G1=15(八进制) = 1 + D + D^3
        output = []
        state = 0
        for bit in input_bits:
            feedback = (state >> 0) ^ (state >> 2)  # 1 + D^3
            output_bit = (bit ^ feedback) & 1
            output.append(output_bit)
            state = ((state << 1) | bit) & 0b111  # 保持3位状态
        return np.array(output)
    
    def encoder2(self, input_bits):
        """第二个卷积编码器 (递归系统卷积码)"""
        # 多项式: G2=13(八进制) = 1 + D^2 + D^3
        output = []
        state = 0
        for bit in input_bits:
            feedback = (state >> 1) ^ (state >> 2)  # D + D^2
            output_bit = (bit ^ feedback) & 1
            output.append(output_bit)
            state = ((state << 1) | bit) & 0b111  # 保持3位状态
        return np.array(output)
    
    def interleaver(self, input_bits):
        """伪随机交织器"""
        np.random.seed(42)  # 固定种子以便重现
        indices = np.random.permutation(len(input_bits))
        return input_bits[indices], indices
    
    def deinterleaver(self, input_bits, indices):
        """解交织器"""
        inverse_indices = np.argsort(indices)
        return input_bits[inverse_indices]
    
    def awgn_channel(self, coded_bits, snr_db):
        """添加高斯白噪声"""
        snr = 10**(snr_db / 10)
        noise_var = 1/(2*snr)  # 假设单位信号功率
        noise = np.sqrt(noise_var) * np.random.randn(len(coded_bits))
        received = 2*coded_bits - 1 + noise  # BPSK调制
        return received
    
    def bcjr_decoder(self, received, encoder_func, prior=None):
        """简化的BCJR解码器"""
        if prior is None:
            prior = np.zeros_like(received)
        
        # 这里应该是完整的BCJR实现，简化起见用LLR近似
        llr = 2 * received / (0.5**2)  # 假设噪声方差0.5
        if encoder_func == self.encoder1:
            llr += 0.5 * prior  # 使用先验信息
        else:
            llr += 0.5 * prior
            
        decoded_bits = (llr > 0).astype(int)
        extrinsic = llr - prior - 2 * received  # 近似外部信息
        
        return decoded_bits, extrinsic
    
    def show_results(self, info_bits, decoded_bits, ber_history):

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei','Noto Sans CJK SC']
        plt.rcParams['axes.unicode_minus'] = False

        # 文本结果显示
        errors = np.sum(decoded_bits != info_bits)
        ber = errors / len(info_bits)
        
        result_str = f"仿真结果:\n"
        result_str += f"信息块长度: {len(info_bits)} bits\n"
        result_str += f"SNR: {self.SNR_dB} dB\n"
        result_str += f"约束长度: {self.K}\n"
        result_str += f"迭代次数: {self.iterations}\n"
        result_str += f"最终误码数: {errors}\n"
        result_str += f"最终误码率(BER): {ber:.6f}\n\n"
        result_str += "迭代过程中的误码率变化:\n"
        
        for i, ber in enumerate(ber_history):
            result_str += f"迭代 {i+1}: BER = {ber:.6f}\n"
        
        self.result_text.setPlainText(result_str)
        
        # 图形结果显示
        self.figure.clear()
        
        # 误码率变化曲线
        ax1 = self.figure.add_subplot(211)
        ax1.plot(range(1, len(ber_history)+1), ber_history, 'bo-')
        ax1.set_xlabel('迭代次数')
        ax1.set_ylabel('误码率(BER)')
        ax1.set_title('Turbo解码迭代性能')
        ax1.grid(True)
        
        # 原始信息和解码信息对比(只显示前50位)
        ax2 = self.figure.add_subplot(212)
        n_show = min(50, len(info_bits))
        ax2.stem(range(n_show), info_bits[:n_show], 'b', markerfmt='bo', label='原始信息')
        ax2.stem(range(n_show), decoded_bits[:n_show], 'r', markerfmt='rx', label='解码信息')
        ax2.set_xlabel('比特位置')
        ax2.set_ylabel('比特值')
        ax2.set_title('原始信息与解码信息对比(前50位)')
        ax2.legend()
        ax2.grid(True)
        
        self.figure.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication([])
    window = TurboCodeSimulator()
    window.show()
    app.exec_()