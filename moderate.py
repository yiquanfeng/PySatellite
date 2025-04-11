import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QGroupBox, QLabel, QComboBox, 
                              QPushButton, QSlider, QSpinBox, QTabWidget)
from PySide2.QtCore import Qt
from scipy.signal import hilbert, butter, filtfilt


class CompleteModulationSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("卫星通信信号调制与解调模拟器 (完整版)")
        self.setGeometry(100, 100, 1200, 900)
        
        # 初始化参数
        self.carrier_freq = 10  # 载波频率 (Hz)
        self.bit_rate = 2       # 比特率 (bits/sec)
        self.sampling_rate = 1000  # 采样率 (Hz)
        self.modulation_type = "ASK"  # 调制类型
        self.bits = [1, 0, 1, 1, 0, 1, 0, 0]  # 要传输的比特序列
        
        # ASK特定参数
        self.ask_high_amp = 1.0  # 高电平幅度
        self.ask_low_amp = 0.2   # 低电平幅度
        
        # FSK特定参数
        self.freq_deviation = 5  # 频偏 (Hz)
        
        # PSK特定参数
        self.phase_shift = np.pi  # 相移 (弧度)
        
        self.init_ui()
        
    def init_ui(self):
        # 主控件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 左侧控制面板
        control_panel = QGroupBox("调制参数")
        control_layout = QVBoxLayout()
        
        # 调制类型选择
        mod_label = QLabel("调制类型:")
        self.mod_combo = QComboBox()
        self.mod_combo.addItems(["ASK", "FSK", "PSK"])
        self.mod_combo.currentTextChanged.connect(self.update_modulation_type)
        
        # 载波频率设置
        freq_label = QLabel("载波频率 (Hz):")
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(5, 20)
        self.freq_slider.setValue(self.carrier_freq)
        self.freq_slider.valueChanged.connect(self.update_carrier_freq)
        self.freq_value = QLabel(str(self.carrier_freq))
        
        # 比特率设置
        bitrate_label = QLabel("比特率 (bits/sec):")
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(1, 5)
        self.bitrate_spin.setValue(self.bit_rate)
        self.bitrate_spin.valueChanged.connect(self.update_bit_rate)
        
        # ASK参数
        self.ask_group = QGroupBox("ASK参数")
        ask_layout = QVBoxLayout()
        high_amp_label = QLabel("高电平幅度:")
        self.high_amp_slider = QSlider(Qt.Horizontal)
        self.high_amp_slider.setRange(1, 10)
        self.high_amp_slider.setValue(int(self.ask_high_amp * 10))
        self.high_amp_slider.valueChanged.connect(self.update_ask_high_amp)
        self.high_amp_value = QLabel(f"{self.ask_high_amp:.1f}")
        
        low_amp_label = QLabel("低电平幅度:")
        self.low_amp_slider = QSlider(Qt.Horizontal)
        self.low_amp_slider.setRange(0, 5)
        self.low_amp_slider.setValue(int(self.ask_low_amp * 10))
        self.low_amp_slider.valueChanged.connect(self.update_ask_low_amp)
        self.low_amp_value = QLabel(f"{self.ask_low_amp:.1f}")
        
        ask_layout.addWidget(high_amp_label)
        ask_layout.addWidget(self.high_amp_slider)
        ask_layout.addWidget(self.high_amp_value)
        ask_layout.addWidget(low_amp_label)
        ask_layout.addWidget(self.low_amp_slider)
        ask_layout.addWidget(self.low_amp_value)
        self.ask_group.setLayout(ask_layout)
        
        # FSK参数
        self.fsk_group = QGroupBox("FSK参数")
        fsk_layout = QVBoxLayout()
        freq_dev_label = QLabel("频偏 (Hz):")
        self.freq_dev_slider = QSlider(Qt.Horizontal)
        self.freq_dev_slider.setRange(1, 10)
        self.freq_dev_slider.setValue(self.freq_deviation)
        self.freq_dev_slider.valueChanged.connect(self.update_freq_deviation)
        self.freq_dev_value = QLabel(str(self.freq_deviation))
        fsk_layout.addWidget(freq_dev_label)
        fsk_layout.addWidget(self.freq_dev_slider)
        fsk_layout.addWidget(self.freq_dev_value)
        self.fsk_group.setLayout(fsk_layout)
        
        # PSK参数
        self.psk_group = QGroupBox("PSK参数")
        psk_layout = QVBoxLayout()
        phase_shift_label = QLabel("相移 (度):")
        self.phase_shift_slider = QSlider(Qt.Horizontal)
        self.phase_shift_slider.setRange(0, 360)
        self.phase_shift_slider.setValue(int(self.phase_shift * 180 / np.pi))
        self.phase_shift_slider.valueChanged.connect(self.update_phase_shift)
        self.phase_shift_value = QLabel(f"{int(self.phase_shift * 180 / np.pi)}°")
        psk_layout.addWidget(phase_shift_label)
        psk_layout.addWidget(self.phase_shift_slider)
        psk_layout.addWidget(self.phase_shift_value)
        self.psk_group.setLayout(psk_layout)
        
        # 随机比特生成按钮
        self.random_bits_btn = QPushButton("生成随机比特序列")
        self.random_bits_btn.clicked.connect(self.generate_random_bits)
        
        # 添加控件到控制面板
        control_layout.addWidget(mod_label)
        control_layout.addWidget(self.mod_combo)
        control_layout.addWidget(freq_label)
        control_layout.addWidget(self.freq_slider)
        control_layout.addWidget(self.freq_value)
        control_layout.addWidget(bitrate_label)
        control_layout.addWidget(self.bitrate_spin)
        control_layout.addWidget(self.ask_group)
        control_layout.addWidget(self.fsk_group)
        control_layout.addWidget(self.psk_group)
        control_layout.addWidget(self.random_bits_btn)
        control_layout.addStretch()
        
        control_panel.setLayout(control_layout)
        
        # 右侧图形显示区域
        plot_panel = QWidget()
        plot_layout = QVBoxLayout()
        
        # 使用TabWidget组织不同的图形视图
        self.tab_widget = QTabWidget()
        
        # 信号时域图
        self.time_figure, (self.ax1, self.ax2, self.ax3, self.ax4) = plt.subplots(4, 1, figsize=(10, 8))
        self.time_canvas = FigureCanvas(self.time_figure)
        
        # 信号频域图
        self.freq_figure, (self.ax5, self.ax6) = plt.subplots(2, 1, figsize=(10, 6))
        self.freq_canvas = FigureCanvas(self.freq_figure)
        
        # 相位/幅度变化图
        self.attr_figure, self.ax7 = plt.subplots(1, 1, figsize=(10, 4))
        self.attr_canvas = FigureCanvas(self.attr_figure)
        
        # 添加标签页
        self.tab_widget.addTab(self.time_canvas, "时域信号")
        self.tab_widget.addTab(self.freq_canvas, "频域分析")
        self.tab_widget.addTab(self.attr_canvas, "属性变化")
        
        plot_layout.addWidget(self.tab_widget)
        plot_panel.setLayout(plot_layout)
        
        # 将左右面板添加到主布局
        main_layout.addWidget(control_panel, stretch=1)
        main_layout.addWidget(plot_panel, stretch=3)
        
        # 初始更新UI状态
        self.update_ui_state()
        self.update_plots()
    
    def update_ui_state(self):
        """根据当前调制类型显示/隐藏相关参数组"""
        self.ask_group.setVisible(self.modulation_type == "ASK")
        self.fsk_group.setVisible(self.modulation_type == "FSK")
        self.psk_group.setVisible(self.modulation_type == "PSK")
        
        # 设置属性变化图的标题
        if self.modulation_type == "PSK":
            self.attr_canvas.figure.axes[0].set_title('载波相位变化')
        elif self.modulation_type == "ASK":
            self.attr_canvas.figure.axes[0].set_title('信号幅度变化')
        else:
            self.attr_canvas.figure.axes[0].set_title('瞬时频率变化')
    
    def update_modulation_type(self, mod_type):
        self.modulation_type = mod_type
        self.update_ui_state()
        self.update_plots()
    
    def update_carrier_freq(self, freq):
        self.carrier_freq = freq
        self.freq_value.setText(str(freq))
        self.update_plots()
    
    def update_bit_rate(self, rate):
        self.bit_rate = rate
        self.update_plots()
    
    def update_ask_high_amp(self, value):
        self.ask_high_amp = value / 10.0
        self.high_amp_value.setText(f"{self.ask_high_amp:.1f}")
        self.update_plots()
    
    def update_ask_low_amp(self, value):
        self.ask_low_amp = value / 10.0
        self.low_amp_value.setText(f"{self.ask_low_amp:.1f}")
        self.update_plots()
    
    def update_freq_deviation(self, dev):
        self.freq_deviation = dev
        self.freq_dev_value.setText(str(dev))
        self.update_plots()
    
    def update_phase_shift(self, angle):
        self.phase_shift = angle * np.pi / 180
        self.phase_shift_value.setText(f"{angle}°")
        self.update_plots()
    
    def generate_random_bits(self):
        # 生成8位随机比特序列
        self.bits = np.random.randint(0, 2, 8).tolist()
        self.update_plots()
    
    def update_plots(self):
        # 计算时间轴
        bit_duration = 1 / self.bit_rate  # 每个比特的持续时间
        t_per_bit = np.linspace(0, bit_duration, int(self.sampling_rate / self.bit_rate))
        t = np.array([])
        
        # 生成数字信号
        digital_signal = np.array([])
        for bit in self.bits:
            digital_signal = np.append(digital_signal, bit * np.ones(len(t_per_bit)))
            t = np.append(t, t_per_bit + len(t) / self.sampling_rate)
        
        # 生成载波信号
        carrier_signal = np.sin(2 * np.pi * self.carrier_freq * t)
        
        # 根据调制类型生成调制信号
        if self.modulation_type == "ASK":
            # ASK调制
            modulated_signal = np.zeros_like(t)
            amplitude_history = np.zeros_like(t)
            
            for i, bit in enumerate(self.bits):
                start = i * len(t_per_bit)
                end = (i + 1) * len(t_per_bit)
                amplitude = self.ask_high_amp if bit == 1 else self.ask_low_amp
                modulated_signal[start:end] = amplitude * carrier_signal[start:end]
                amplitude_history[start:end] = amplitude
            
            # ASK解调 - 包络检波
            rectified_signal = np.abs(modulated_signal)
            # 低通滤波
            demodulated_signal = self.lowpass_filter(rectified_signal, cutoff=2*self.bit_rate)
            # 二进制决策
            threshold = (self.ask_high_amp + self.ask_low_amp) / 2
            demodulated_signal = [1 if x > threshold else 0 for x in demodulated_signal]
            
        elif self.modulation_type == "FSK":
            # FSK调制 - 相位连续的频率调制
            freq1 = self.carrier_freq + self.freq_deviation/2  # 比特1的频率
            freq0 = self.carrier_freq - self.freq_deviation/2  # 比特0的频率
            
            phase = 0
            modulated_signal = np.zeros_like(t)
            instantaneous_freq = np.zeros_like(t)
            
            for i, bit in enumerate(self.bits):
                start = i * len(t_per_bit)
                end = (i + 1) * len(t_per_bit)
                current_freq = freq1 if bit == 1 else freq0
                phase_increment = 2 * np.pi * current_freq * (t_per_bit[1] - t_per_bit[0])
                
                for j in range(start, end):
                    phase += phase_increment
                    modulated_signal[j] = np.sin(phase)
                    instantaneous_freq[j] = current_freq
            
            # FSK解调 - 频率判别法
            demodulated_signal = np.zeros_like(t)
            threshold_freq = self.carrier_freq
            for i in range(len(t)):
                demodulated_signal[i] = 1 if instantaneous_freq[i] > threshold_freq else 0
            
        elif self.modulation_type == "PSK":
            # PSK调制 - 精确相位变化
            modulated_signal = np.zeros_like(t)
            phase = 0
            phase_history = np.zeros_like(t)
            
            for i, bit in enumerate(self.bits):
                start = i * len(t_per_bit)
                end = (i + 1) * len(t_per_bit)
                # 根据比特值决定相位
                target_phase = 0 if bit == 1 else self.phase_shift
                
                for j in range(start, end):
                    # 平滑相位过渡
                    if j == start:
                        phase = target_phase
                    modulated_signal[j] = np.sin(2 * np.pi * self.carrier_freq * t[j] + phase)
                    phase_history[j] = phase
            
            # PSK解调 - 相干解调
            demod_carrier = np.sin(2 * np.pi * self.carrier_freq * t)
            mixed_signal = modulated_signal * demod_carrier
            # 低通滤波
            demodulated_signal = self.lowpass_filter(mixed_signal, cutoff=2*self.bit_rate)
            # 二进制决策
            demodulated_signal = [1 if x > 0 else 0 for x in demodulated_signal]
        
        # 绘制时域信号
        self.draw_time_domain(t, digital_signal, carrier_signal, modulated_signal, demodulated_signal)
        
        # 绘制频域分析
        self.draw_frequency_domain(t, modulated_signal)
        
        # 绘制属性变化图
        if self.modulation_type == "ASK":
            self.draw_attribute_changes(t, amplitude_history, "幅度", "幅度变化")
        elif self.modulation_type == "FSK":
            self.draw_attribute_changes(t, instantaneous_freq, "频率 (Hz)", "瞬时频率变化")
        elif self.modulation_type == "PSK":
            self.draw_attribute_changes(t, phase_history * 180 / np.pi, "相位 (度)", "载波相位变化")
        
        # 显示比特序列
        bits_str = ' '.join(map(str, self.bits))
        self.statusBar().showMessage(f"当前比特序列: {bits_str}")
    
    def lowpass_filter(self, signal, cutoff, order=5):
        """应用低通滤波器"""
        nyquist = 0.5 * self.sampling_rate
        normal_cutoff = cutoff / nyquist
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        filtered_signal = filtfilt(b, a, signal)
        return filtered_signal
    
    def draw_time_domain(self, t, digital_signal, carrier_signal, modulated_signal, demodulated_signal):
        """绘制时域信号图"""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # 数字信号
        self.ax1.plot(t, digital_signal, 'b')
        self.ax1.set_title('数字信号')
        self.ax1.set_ylim(-0.5, 1.5)
        self.ax1.grid(True)
        
        # 载波信号
        self.ax2.plot(t, carrier_signal, 'g')
        self.ax2.set_title(f'载波信号 ({self.carrier_freq}Hz)')
        self.ax2.grid(True)
        
        # 调制信号
        self.ax3.plot(t, modulated_signal, 'r')
        mod_title = {
            "ASK": f"ASK调制信号 (高电平幅度={self.ask_high_amp:.1f}, 低电平幅度={self.ask_low_amp:.1f})",
            "FSK": f"FSK调制信号 (f1={self.carrier_freq+self.freq_deviation/2:.1f}Hz, f0={self.carrier_freq-self.freq_deviation/2:.1f}Hz)",
            "PSK": f"PSK调制信号 (相位差={int(self.phase_shift*180/np.pi)}°)"
        }[self.modulation_type]
        self.ax3.set_title(mod_title)
        self.ax3.grid(True)
        
        # 解调信号
        self.ax4.plot(t, demodulated_signal, 'm')
        self.ax4.set_title('解调信号')
        self.ax4.set_ylim(-0.5, 1.5)
        self.ax4.grid(True)
        
        # 标记比特边界
        bit_duration = 1 / self.bit_rate
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            for i in range(len(self.bits)+1):
                ax.axvline(i*bit_duration, color='gray', linestyle='--', alpha=0.3)
        
        self.time_figure.tight_layout()
        self.time_canvas.draw()
    
    def draw_frequency_domain(self, t, modulated_signal):
        """绘制频域分析图"""
        self.ax5.clear()
        self.ax6.clear()
        
        # 计算FFT
        n = len(modulated_signal)
        fft_result = np.fft.fft(modulated_signal)
        freq = np.fft.fftfreq(n, d=1/self.sampling_rate)
        
        # 绘制幅度谱
        self.ax5.plot(freq[:n//2], np.abs(fft_result[:n//2]), 'b')
        self.ax5.set_title('调制信号频谱')
        self.ax5.set_xlabel('频率 (Hz)')
        self.ax5.set_ylabel('幅度')
        self.ax5.grid(True)
        
        # 如果是FSK，绘制瞬时频率
        if self.modulation_type == "FSK":
            # 计算瞬时频率 (使用解析信号方法)
            analytic_signal = hilbert(modulated_signal)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal))
            instantaneous_freq = np.diff(instantaneous_phase) / (2.0*np.pi) * self.sampling_rate
            
            # 由于差分，时间轴需要调整
            t_inst = t[:-1] + (t[1]-t[0])/2
            
            self.ax6.plot(t_inst, instantaneous_freq, 'r')
            self.ax6.set_title('瞬时频率变化')
            self.ax6.set_xlabel('时间 (s)')
            self.ax6.set_ylabel('频率 (Hz)')
            self.ax6.grid(True)
        
        self.freq_figure.tight_layout()
        self.freq_canvas.draw()
    
    def draw_attribute_changes(self, t, attribute_values, ylabel, title):
        """绘制属性变化图(幅度/频率/相位)"""
        self.ax7.clear()
        
        # 绘制属性变化
        self.ax7.plot(t, attribute_values, 'purple')
        self.ax7.set_title(title)
        self.ax7.set_xlabel('时间 (s)')
        self.ax7.set_ylabel(ylabel)
        self.ax7.grid(True)
        
        # 标记比特边界
        bit_duration = 1 / self.bit_rate
        for i in range(len(self.bits)+1):
            self.ax7.axvline(i*bit_duration, color='gray', linestyle='--', alpha=0.5)
        
        self.attr_figure.tight_layout()
        self.attr_canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompleteModulationSimulator()
    window.show()
    sys.exit(app.exec_())