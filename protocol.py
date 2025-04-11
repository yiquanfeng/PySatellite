import sys
import numpy as np
from PySide2.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QPushButton, QLabel, QTextEdit, QGroupBox, 
                             QLineEdit, QHBoxLayout)
from PySide2.QtCore import Qt

class ProtocolSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简化协议仿真系统")
        self.setGeometry(100, 100, 800, 600)
        
        self.frame_counter = 0
        self.init_ui()
        
    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 帧结构图示
        frame_struct = QLabel(
            "帧结构: | 同步头(0xAA 8bit) | 帧号(4bit) | 数据(280bit) | CRC-8 |")
        layout.addWidget(frame_struct)
        
        # 输入区域
        input_group = QGroupBox("输入数据")
        input_layout = QVBoxLayout()
        
        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("输入要发送的数据（ASCII或Hex）")
        input_layout.addWidget(self.data_input)
        
        send_btn = QPushButton("发送帧")
        send_btn.clicked.connect(self.send_frame)
        input_layout.addWidget(send_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 输出区域
        output_group = QGroupBox("协议处理过程")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout = QVBoxLayout()
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 状态监控
        status_group = QGroupBox("状态监控")
        status_layout = QHBoxLayout()
        
        self.frame_counter_label = QLabel("帧计数: 0")
        self.crc_status_label = QLabel("最后CRC: -")
        
        status_layout.addWidget(self.frame_counter_label)
        status_layout.addWidget(self.crc_status_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    
    def crc8(self, data):
        """计算CRC-8 (多项式x⁸+x²+x+1)"""
        crc = 0
        poly = 0x07  # x⁸ + x² + x + 1 (忽略最高位)
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ poly
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    def send_frame(self):
        """组帧并发送"""
        try:
            # 1. 获取输入数据
            input_data = self.data_input.text()
            
            # 尝试解析为Hex，失败则当作ASCII
            try:
                if input_data.startswith("0x"):
                    data_bytes = bytes.fromhex(input_data[2:])
                else:
                    data_bytes = bytes.fromhex(input_data)
            except:
                data_bytes = input_data.encode('ascii')
            
            # 2. 组帧
            sync_header = 0xAA
            frame_num = self.frame_counter % 16  # 4bit帧号循环
            
            # 数据填充/截断为280bit (35字节)
            data_bytes = data_bytes[:35]
            data_bytes = data_bytes.ljust(35, b'\x00')
            
            # 计算CRC (包含同步头、帧号和数据)
            crc_data = bytes([sync_header, frame_num]) + data_bytes
            crc = self.crc8(crc_data)
            
            # 3. 构造完整帧
            frame = bytes([sync_header, frame_num]) + data_bytes + bytes([crc])
            
            # 4. 模拟接收端解析
            self.parse_frame(frame)
            
            # 5. 更新状态
            self.frame_counter += 1
            self.frame_counter_label.setText(f"帧计数: {self.frame_counter}")
            
        except Exception as e:
            self.output_text.append(f"错误: {str(e)}")
    
    def parse_frame(self, frame):
        """解析接收到的帧"""
        # 1. 检查同步头
        if frame[0] != 0xAA:
            self.output_text.append("错误: 同步头不匹配！")
            return
        
        # 2. 提取字段
        frame_num = frame[1] & 0x0F  # 取低4位
        data = frame[2:-1]
        received_crc = frame[-1]
        
        # 3. 计算CRC校验
        calculated_crc = self.crc8(frame[:-1])
        crc_ok = (received_crc == calculated_crc)
        
        # 4. 显示结果
        self.output_text.append(
            f"帧 {frame_num}: "
            f"数据[{len(data)}字节]={data[:8].hex()}... "
            f"接收CRC=0x{received_crc:02X} "
            f"计算CRC=0x{calculated_crc:02X} "
            f"({'通过' if crc_ok else '失败'})"
        )
        
        # 更新CRC状态
        status = "✓" if crc_ok else "✗"
        self.crc_status_label.setText(f"最后CRC: 0x{received_crc:02X} {status}")
        
        # 5. 如果校验通过，处理数据
        if crc_ok:
            self.process_data(data)
    
    def process_data(self, data):
        """处理有效数据（示例）"""
        try:
            # 尝试解码为ASCII，非ASCII显示为Hex
            try:
                decoded = data.decode('ascii').strip('\x00')
                self.output_text.append(f"解码数据(ASCII): {decoded}")
            except:
                self.output_text.append(f"解码数据(Hex): {data.hex()}")
        except Exception as e:
            self.output_text.append(f"数据处理错误: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProtocolSimulator()
    window.show()
    sys.exit(app.exec_())