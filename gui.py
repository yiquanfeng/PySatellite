import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                             QVBoxLayout, QHBoxLayout, QWidget, QComboBox, 
                             QFrame, QFileDialog, QGroupBox, QSplitter, 
                             QTextEdit, QStackedWidget, QProgressDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QFont

import ui_main
import text
import sound

class AudioProcessingWorker(QObject):
    """用于处理音频的工作线程"""
    finished = pyqtSignal(tuple)  # 成功时发出信号(y, sr)
    error = pyqtSignal(str)       # 错误时发出信号(错误信息)
    progress = pyqtSignal(int)    # 进度信号
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        
    def process_audio(self):
        try:
            # 使用librosa加载音频，但限制为前30秒
            import librosa
            y, sr = librosa.load(self.filename, sr=None, duration=30)
            
            # 如果是立体声，转换为单声道用于显示
            if y.ndim > 1:
                y = np.mean(y, axis=1)
                
            self.finished.emit((y, sr))
            
        except Exception as e:
            self.error.emit(str(e))


class SatelliteCommunicationSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
         # 用于存储线程
        self.thread = None
        self.audio_worker = None

    def initUI(self):
        # set the matplotlib font
        font = 'SimHei'
        mpl.rcParams['font.sans-serif'] = [font] + mpl.rcParams['font.sans-serif']
        # 解决负号显示问题
        mpl.rcParams['axes.unicode_minus'] = False

        # 设置窗口标题和大小
        self.setWindowTitle('卫星通信模拟器')
        self.setGeometry(100, 100, 1600, 1000)
        
        # 创建主布局
        mainLayout = QVBoxLayout()
        # 顶部控件布局
        topLayout = QHBoxLayout()
        
        # 左上角：上传类型选择部分
        uploadGroupBox = QGroupBox("上传类型")
        uploadGroupBox.setMaximumWidth(400)
        uploadLayout = QVBoxLayout()
        self.uploadTypeComboBox = QComboBox() ## 下拉菜单
        self.uploadTypeComboBox.setStyleSheet("padding: 5px;")
        uploadTypes = ["文字", "图片", "语音"]
        self.uploadTypeComboBox.addItems(uploadTypes)
        self.uploadTypeComboBox.currentIndexChanged.connect(self.uploadTypeChanged)
        
        # 添加上传按钮
        self.uploadButton = QPushButton("选择文件")
        self.uploadButton.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.uploadButton.clicked.connect(self.uploadFile)
        
        # 添加控件到布局
        uploadLayout.addWidget(self.uploadTypeComboBox)
        uploadLayout.addWidget(self.uploadButton)
        uploadGroupBox.setLayout(uploadLayout)
        
        # 右上角：阶段选择部分
        stageGroupBox = QGroupBox("通信阶段")
        stageGroupBox.setMaximumWidth(200)
        stageLayout = QVBoxLayout()
        
        self.stageComboBox = QComboBox()
        self.stageComboBox.setStyleSheet("padding: 5px;")
        stages = ["AD转换", "DA转换", "编码", '解码', "协议层", '解析协议', "调制", "解调", "模拟信道"]
        self.stageComboBox.addItems(stages)
        self.stageComboBox.currentIndexChanged.connect(self.stageChanged)
        
        stageLayout.addWidget(self.stageComboBox)
        stageGroupBox.setLayout(stageLayout)
        
        # 添加到顶部布局
        topLayout.addWidget(uploadGroupBox)
        topLayout.addStretch(1)  # 添加弹性空间
        topLayout.addWidget(stageGroupBox)
        
        # 中间：显示区域
        middleLayout = QHBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧显示框
        self.leftDisplayFrame = QFrame()
        self.leftDisplayFrame.setFrameShape(QFrame.StyledPanel)
        self.leftDisplayFrame.setMinimumSize(400, 350)
        self.leftDisplayFrame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 4px;")
        leftFrameLayout = QVBoxLayout()
        
        leftTitleLabel = QLabel("原始数据")
        leftTitleLabel.setAlignment(Qt.AlignCenter)
        leftTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
        leftTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
        
        # 使用堆叠窗口部件管理不同类型的显示内容
        self.leftContentStack = QStackedWidget()
        
        # 1. 文本编辑区域 - 用于文字输入或显示
        self.textEditArea = QTextEdit()
        self.textEditArea.setStyleSheet("padding: 10px;")
        self.textEditArea.setPlaceholderText("在此输入文字或上传文本文件...")
        
        # 2. 图片显示区域
        self.imageDisplayWidget = QWidget()
        imageLayout = QVBoxLayout()
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        imageLayout.addWidget(self.imageLabel)
        self.imageDisplayWidget.setLayout(imageLayout)
        
        # 3. 音频振幅图显示区域
        self.audioDisplayWidget = QWidget()
        audioLayout = QVBoxLayout()
        
        # 添加音频信息标签 - 确保此部分代码存在
        self.audioInfoLabel = QLabel("尚未加载音频文件")
        self.audioInfoLabel.setAlignment(Qt.AlignCenter)
        self.audioInfoLabel.setStyleSheet("color: #666; font-style: italic;")
        audioLayout.addWidget(self.audioInfoLabel)
        
        self.audioFigure = plt.figure(figsize=(5, 4))
        self.audioCanvas = FigureCanvas(self.audioFigure)
        audioLayout.addWidget(self.audioCanvas)
        self.audioDisplayWidget.setLayout(audioLayout)
        
        # 将各个显示区域添加到堆叠窗口部件
        self.leftContentStack.addWidget(self.textEditArea)        # 索引0
        self.leftContentStack.addWidget(self.imageDisplayWidget)  # 索引1
        self.leftContentStack.addWidget(self.audioDisplayWidget)  # 索引2
        
        # 初始显示文本区域
        self.leftContentStack.setCurrentIndex(0)
        
        leftFrameLayout.addWidget(leftTitleLabel)
        leftFrameLayout.addWidget(self.leftContentStack)
        self.leftDisplayFrame.setLayout(leftFrameLayout)
        
        # 右侧显示框
        self.rightDisplayFrame = QFrame()
        self.rightDisplayFrame.setFrameShape(QFrame.StyledPanel)
        self.rightDisplayFrame.setMinimumSize(400, 350)
        self.rightDisplayFrame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 4px;")
        rightFrameLayout = QVBoxLayout()
        
        rightTitleLabel = QLabel("处理后数据")
        rightTitleLabel.setAlignment(Qt.AlignCenter)
        rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
        rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
        
        # 使用QTextEdit来显示右侧内容
        self.rightDisplayContent = QTextEdit()
        self.rightDisplayContent.setReadOnly(True)
        self.rightDisplayContent.setStyleSheet("padding: 10px;")
        self.rightDisplayContent.setPlaceholderText("处理后的数据将显示在这里")
        
        rightFrameLayout.addWidget(rightTitleLabel)
        rightFrameLayout.addWidget(self.rightDisplayContent)
        self.rightDisplayFrame.setLayout(rightFrameLayout)
        
        # 添加到分割器
        splitter.addWidget(self.leftDisplayFrame)
        splitter.addWidget(self.rightDisplayFrame)
        splitter.setSizes([500, 500])  # 设置初始大小
        
        # 添加分割器到中间布局
        middleLayout.addWidget(splitter)
        
        # 底部：开始模拟按钮
        bottomLayout = QHBoxLayout()
        
        # 状态标签
        self.statusLabel = QLabel("就绪，等待上传数据...")
        self.statusLabel.setStyleSheet("padding: 5px; background-color: #e9ecef; border-radius: 3px;")
        
        # 模拟按钮
        self.simulateButton = QPushButton("开始模拟")
        self.simulateButton.setMinimumHeight(40)
        self.simulateButton.setMinimumWidth(150)
        self.simulateButton.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton:pressed {
                background-color: #0062CC;
            }
        """)
        self.simulateButton.clicked.connect(self.startSimulation)
        
        bottomLayout.addWidget(self.statusLabel)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.simulateButton)
        
        # 添加所有布局到主布局
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(middleLayout, 1)  # 设置中间部分可扩展
        mainLayout.addLayout(bottomLayout)
        
        # 创建中央窗口部件并设置布局
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QComboBox {
                padding: 6px;
            }
            QLabel {
                color: #444;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)
        
        # 存储当前文件路径
        self.currentFile = None
        self.currentFileType = None
        
        # 初始化上传类型
        self.uploadTypeChanged(0)
    
    def uploadTypeChanged(self, index):
        """当上传类型改变时调用"""
        self.leftContentStack.setCurrentIndex(index)
        
        # 更新按钮文字
        if index == 0:  # 文字
            self.uploadButton.setText("输入文字或者选择文本文件")
            self.currentFileType = "text"
        elif index == 1:  # 图片
            self.uploadButton.setText("选择图像文件")
            self.currentFileType = "image"
        elif index == 2:  # 语音
            self.uploadButton.setText("选择音频文件")
            self.currentFileType = "audio"
            
        self.statusLabel.setText(f"已选择上传类型: {self.uploadTypeComboBox.currentText()}")
    
    def uploadFile(self):
        # 根据选中的上传类型，打开相应的文件对话框
        current_type_index = self.uploadTypeComboBox.currentIndex()
        if current_type_index == 1:  # 图片
            fileName, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "", "图像文件 (*.png *.jpg *.jpeg *.bmp)")
            if fileName:
                pixmap = QPixmap(fileName)
                # 调整图片大小以适应显示区域
                pixmap = pixmap.scaled(self.leftDisplayFrame.width() - 40, self.leftDisplayFrame.height() - 80, 
                                        Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # 显示图片
                self.imageLabel.setPixmap(pixmap)
                self.statusLabel.setText(f"已上传图片: {fileName.split('/')[-1]}")
                self.currentFile = fileName
        
        elif current_type_index == 0:  # 文字
            fileName, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "文本文件 (*.txt)")
            if fileName:
                try:
                    with open(fileName, 'r', encoding='utf-8') as file:
                        text = file.read()                   
                    # 显示文本
                    self.textEditArea.setPlainText(text)
                    self.statusLabel.setText(f"已上传文本: {fileName.split('/')[-1]}")
                    self.currentFile = fileName
                except Exception as e:
                    self.textEditArea.setPlainText(f"无法读取文件: {str(e)}")
                    self.statusLabel.setText("文件读取失败")
        
        elif current_type_index == 2:  # 音频
            fileName, _ = QFileDialog.getOpenFileName(
                self, 
                "选择音频文件", 
                "", 
                "音频文件 (*.mp3 *.wav *.flac)"  # 添加了flac格式支持
            )
            if fileName:
                # 显示加载信息
                self.audioInfoLabel.setText(f"正在加载音频文件: {os.path.basename(fileName)}")
                self.statusLabel.setText("正在处理音频文件...")
                
                # 禁用上传按钮，防止重复操作
                self.uploadButton.setEnabled(False)
                
                # 创建工作线程处理音频
                self.audio_worker = AudioProcessingWorker(fileName)
                self.thread = QThread()
                self.audio_worker.moveToThread(self.thread)
                
                # 连接信号和槽
                self.thread.started.connect(self.audio_worker.process_audio)
                self.audio_worker.finished.connect(self.onAudioProcessed)
                self.audio_worker.error.connect(self.onAudioProcessError)
                self.audio_worker.finished.connect(self.thread.quit)
                self.audio_worker.finished.connect(self.audio_worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.thread.finished.connect(lambda: self.uploadButton.setEnabled(True))
                
                # 启动线程
                self.thread.start()
                
                # 保存文件信息
                self.currentFile = fileName
                self.currentFileType = "audio"
    
    def onAudioProcessed(self, data):
        """音频处理完成后的回调函数"""
        y, sr = data
        try:
            # 清除之前的图表
            self.audioFigure.clear()
            
            # 创建新的子图
            ax = self.audioFigure.add_subplot(111)
            
            # 生成时间轴
            time = np.arange(0, len(y[:sr*3])) / sr
            
            # 绘制波形图
            ax.plot(time, y[:sr*3], color='#3498db')
            ax.set_title(f'音频波形: {os.path.basename(self.currentFile)}')
            ax.set_xlabel('时间 (秒)')
            ax.set_ylabel('振幅')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # 添加音频信息
            duration = len(y) / sr / 10
            self.audioInfoLabel.setText(
                f"文件: {os.path.basename(self.currentFile)} | "
                f"采样率: {sr} Hz | "
                f"时长: {duration:.2f} 秒"
            )
            
            # 调整图表布局
            self.audioFigure.tight_layout()
            
            # 更新画布
            self.audioCanvas.draw()
            
            self.statusLabel.setText(f"已上传音频: {os.path.basename(self.currentFile)}")
            
        except Exception as e:
            self.onAudioProcessError(f"绘制音频波形图失败: {str(e)}")
    
    def onAudioProcessError(self, error_message):
        """音频处理出错时的回调函数"""
        # 显示错误信息
        self.audioFigure.clear()
        ax = self.audioFigure.add_subplot(111)
        ax.text(0.5, 0.5, f"无法加载音频文件:\n{error_message}", 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, color='red')
        self.audioCanvas.draw()
        
        self.audioInfoLabel.setText("音频加载失败")
        self.statusLabel.setText("音频处理失败")
        
        # 显示错误对话框
        QMessageBox.warning(self, "音频处理错误", f"处理音频文件时出错:\n{error_message}")
    
    def stageChanged(self):
        selected_stage = self.stageComboBox.currentText()
        self.statusLabel.setText(f"已选择通信阶段: {selected_stage}")

    def get_binary_frames(self):
        _, quan = sound.SoundOperation.sound_ADtrans(self.currentFile)
        return quan
    def get_encoded_text(self) -> str:
        text_tmp = self.textEditArea.toPlainText()
        encoded_text = text.TextOperation.text_encode(text_tmp)
        return encoded_text
    
    def get_decoded_text(self) -> str:
        decoded_text = text.TextOperation.text_decode(self.get_encoded_text())
        return decoded_text
    def get_framed_text(self) -> str:
        return text.TextOperation.text_protocol(self.get_encoded_text())
    def get_deframed_text(self) -> str:
        return text.TextOperation.text_deprotocol(self.get_framed_text())
    def get_modulated_text(self):
        return text.TextOperation.text_modulate(self.get_framed_text(), 10)
    def get_demodulated_text(self):
        fig, received_signal = self.get_channel_text()
        return text.TextOperation.text_demodulate(received_signal)
    def get_channel_text(self):
        fig, signal = self.get_modulated_text()
        return text.TextOperation.text_channel(signal)
    
    def display_data(self, stage:str, index:int):
        canvas = None
        rightDisplayContent = None
        
        if(stage == "encode"):
            if(index == 0):
                rightDisplayContent = QTextEdit()
                rightDisplayContent.setReadOnly(True)
                rightDisplayContent.setStyleSheet("padding: 10px;")
                rightDisplayContent.setPlainText(self.get_encoded_text())
                rightTitleLabel = QLabel("encode info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[1]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("encode info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == 'adtrans'):
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[0]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("ad info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == 'datrans'):
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[6]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("da info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
                # fig, _, _ = sound.SoundOperation.sound_DAtrans(self.get_binary_frames())
                # # 创建画布
                # canvas = FigureCanvas(fig)
                # existing_layout = self.rightDisplayFrame.layout()
                # rightTitleLabel = QLabel("DA转换模拟")
                # rightTitleLabel.setAlignment(Qt.AlignCenter)
                # rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                # rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                # self.statusLabel.setText("DA转换模拟: 已显示信号处理图表")
        elif(stage == 'decode'):
            if(index == 0):
                rightDisplayContent = QTextEdit()
                rightDisplayContent.setReadOnly(True)
                rightDisplayContent.setStyleSheet("padding: 10px;")
                rightDisplayContent.setPlainText(self.get_decoded_text())
                rightTitleLabel = QLabel("decode info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[5]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("decode info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == 'protocol'):
            if(index == 0):
                rightDisplayContent = QTextEdit()
                rightDisplayContent.setReadOnly(True)
                rightDisplayContent.setStyleSheet("padding: 10px;")
                rightDisplayContent.setPlainText(self.get_framed_text())
                rightTitleLabel = QLabel("protocol info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[2]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("protocol info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == 'deprotocol'):
            if(index == 0):
                rightDisplayContent = QTextEdit()
                rightDisplayContent.setReadOnly(True)
                rightDisplayContent.setStyleSheet("padding: 10px;")
                rightDisplayContent.setPlainText(self.get_deframed_text())
                rightTitleLabel = QLabel("deprotocol info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[5]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("deprotocol info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == "modulate"):
            if(index == 0):
                fig, _ = self.get_modulated_text()
                canvas = FigureCanvas(fig)
                rightTitleLabel = QLabel("modulate info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[3]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("modulate info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == "demodulate"):
            if(index == 0):
                fig, string = self.get_demodulated_text()
                rightDisplayContent = QTextEdit()
                rightDisplayContent.setReadOnly(True)
                rightDisplayContent.setStyleSheet("padding: 10px;")
                rightDisplayContent.setPlainText(string)
                rightTitleLabel = QLabel("demodulate info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
            if(index == 2):
                fig_all = ui_main.return_figures()
                fig = fig_all[4]
                canvas = FigureCanvas(fig)
                existing_layout = self.rightDisplayFrame.layout()
                rightTitleLabel = QLabel("demodulate info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")
                self.statusLabel.setText("AD转换模拟: 已显示信号处理图表")
        elif(stage == "channel"):
            if(index == 0):
                fig, _ = self.get_channel_text()
                canvas = FigureCanvas(fig)
                rightTitleLabel = QLabel("channel info")
                rightTitleLabel.setAlignment(Qt.AlignCenter)
                rightTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
                rightTitleLabel.setStyleSheet("color: #333; margin-bottom: 10px;")

        existing_layout = self.rightDisplayFrame.layout()
        while existing_layout.count():
            item = existing_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        existing_layout.addWidget(rightTitleLabel)
        if rightDisplayContent is not None:
            existing_layout.addWidget(rightDisplayContent)
        if canvas is not None:
            existing_layout.addWidget(canvas)


    def startSimulation(self):
        # 检查是否有数据可以模拟
        current_type_index = self.uploadTypeComboBox.currentIndex()
        has_data = False
        
        if current_type_index == 1:  # 图片
            has_data = not self.imageLabel.pixmap().isNull() if self.imageLabel.pixmap() else False
        elif current_type_index == 0:  # 文字
            has_data = len(self.textEditArea.toPlainText()) > 0
        elif current_type_index == 2:  # 音频
            has_data = self.currentFile is not None and self.currentFileType == "audio"
        
        if not has_data:
            self.statusLabel.setText("请先上传或输入数据")
            return
            
        selected_stage = self.stageComboBox.currentText()
        self.statusLabel.setText(f"正在模拟通信过程: {selected_stage}...")

        # 如果选择的是AD/DA转换，则显示信号处理图表
        if selected_stage == "AD转换":
            self.display_data("adtrans", current_type_index)
            return
        if selected_stage == "DA转换":
            self.display_data("datrans", current_type_index)
            return
        if selected_stage == "编码":
            self.display_data("encode", current_type_index)
            return
        if selected_stage == "解码":
            self.display_data("decode", current_type_index)
            return
        if selected_stage == "协议层":
            self.display_data("protocol", current_type_index)
            return
        if selected_stage == "解析协议":
            self.display_data("deprotocol", current_type_index)
            return
        if selected_stage == "调制":
            self.display_data("modulate", current_type_index)
            return
        if selected_stage == "解调":
            self.display_data("demodulate", current_type_index)
            return
        if selected_stage == "模拟信道":
            self.display_data("channel", current_type_index)
            return

        # 获取当前数据类型和内容描述
        data_type = self.uploadTypeComboBox.currentText()
        data_content = ""

        if current_type_index == 1:  # 图片
            data_content = os.path.basename(self.currentFile) if self.currentFile else "当前显示的图片"
        elif current_type_index == 0:  # 文字
            text = self.textEditArea.toPlainText()
            data_content = f"{len(text)} 个字符" if len(text) > 30 else text
        elif current_type_index == 2:  # 音频
         data_content = os.path.basename(self.currentFile) if self.currentFile else "当前音频"
    
    # 在右侧显示模拟信息
        # self.rightDisplayContent.setHtml(f"""
        # <div style="padding: 10px;">
        #     <h3 style="text-align: center; color: #0056b3;">模拟: {selected_stage}</h3>
        #     <hr/>
        #  <p><b>数据类型:</b> {data_type}</p>
        #     <p><b>数据内容:</b> {data_content}</p>
        # <p><b>状态:</b> 模拟进行中...</p>
        # <hr/>
        # <p>这里将显示模拟过程的详细信息</p>
        #     <p style="color: #666; margin-top: 15px;">
        #         模拟流程包括发送端数据处理、卫星转发和接收端信号恢复等步骤。
        #         通过观察每个阶段的数据变化，可以深入理解卫星通信系统的工作原理。
        #     </p>
        # </div>
        # """)

def main():
    app = QApplication(sys.argv)
    simulator = SatelliteCommunicationSimulator()
    simulator.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()