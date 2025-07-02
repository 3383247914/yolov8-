import os
import sys
import cv2
import numpy as np
import torch
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QFileDialog,
    QWidget, QHBoxLayout, QStatusBar, QProgressBar, QMessageBox, QSlider
)
from PySide6.QtGui import QImage, QPixmap, QAction
from PySide6.QtCore import Qt, QThread, Signal
from ultralytics import YOLO

# 修复Qt插件路径问题
def fix_qt_plugin_path():
    try:
        import PySide6
        pyside6_dir = os.path.dirname(PySide6.__file__)
        plugins_path = os.path.join(pyside6_dir, "plugins")
        os.environ["QT_PLUGIN_PATH"] = plugins_path
        if sys.platform == "win32":
            bin_path = os.path.join(pyside6_dir, "bin")
            os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
        print(f"Qt插件路径设置为: {plugins_path}")
    except ImportError:
        print("PySide6未安装")
    except Exception as e:
        print(f"设置Qt插件路径时出错: {str(e)}")

fix_qt_plugin_path()


class DetectionThread(QThread):
    finished = Signal(np.ndarray)
    progress = Signal(int)

    def __init__(self, model, image, confidence):
        super().__init__()
        self.model = model
        self.image = image
        self.confidence = confidence

    def run(self):
        try:
            device = 0 if torch.cuda.is_available() else 'cpu'
            results = self.model(self.image, conf=self.confidence, device=device)
            annotated_frame = results[0].plot()
            boxes = results[0].boxes
            defects_count = len(boxes)
            cv2.putText(annotated_frame, f"Defects: {defects_count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            self.finished.emit(annotated_frame)
        except Exception as e:
            print(f"检测过程中出错: {e}")
            error_image = self.image.copy()
            cv2.putText(error_image, f"检测错误: {str(e)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            self.finished.emit(error_image)


class MetalDefectDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("金属表面缺陷检测系统")
        self.setGeometry(100, 100, 1200, 700)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.showMessage("正在初始化...")

        # 检查GPU
        self.gpu_available = torch.cuda.is_available()
        self.status_bar.showMessage(f"GPU状态: {'可用' if self.gpu_available else '不可用'}", 3000)

        # 菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        open_action = QAction("打开图像", self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 主体布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # 左侧原图显示
        self.original_label = QLabel("原始图像")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setMinimumSize(500, 500)
        self.original_label.setStyleSheet("border: 1px solid gray;")

        # 右侧检测结果
        self.result_label = QLabel("检测结果")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(500, 500)
        self.result_label.setStyleSheet("border: 1px solid gray;")

        # 右侧按钮区
        self.button_layout = QVBoxLayout()
        self.btn_open = QPushButton("打开图像")
        self.btn_detect = QPushButton("运行检测")
        self.btn_detect.setEnabled(False)

        self.gpu_label = QLabel(f"GPU状态: {'已启用' if self.gpu_available else '不可用'}")
        self.gpu_label.setStyleSheet("color: green;" if self.gpu_available else "color: red;")

        # --- 新增：置信度阈值滑块与显示 ---
        self.confidence = 0.5
        self.confidence_label = QLabel(f"置信度阈值: {self.confidence:.2f}")
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(10)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(int(self.confidence * 100))
        self.confidence_slider.setTickInterval(5)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)

        # --- 新增：模型路径显示 ---
        self.model_path = 'models/metal_defect_best.pt'
        self.model_path_label = QLabel(f"当前模型: {self.model_path}")
        self.model_path_label.setStyleSheet("color: blue; font-weight: bold;")
        self.button_layout.addWidget(self.model_path_label)

        self.button_layout.addWidget(self.gpu_label)
        self.button_layout.addWidget(self.confidence_label)
        self.button_layout.addWidget(self.confidence_slider)
        self.button_layout.addWidget(self.btn_open)
        self.button_layout.addWidget(self.btn_detect)
        self.button_layout.addStretch()

        self.layout.addWidget(self.original_label)
        self.layout.addLayout(self.button_layout)
        self.layout.addWidget(self.result_label)

        self.current_image = None

        # 加载模型
        try:
            self.status_bar.showMessage(f"正在加载模型: {self.model_path} ...")
            QApplication.processEvents()
            self.model = YOLO(self.model_path)
            self.status_bar.showMessage(f"模型加载成功: {self.model_path}", 3000)
        except Exception as e:
            self.status_bar.showMessage("模型加载失败", 3000)
            QMessageBox.critical(self, "模型加载错误", f"无法加载模型: {str(e)}")
            print(f"模型加载错误: {e}")
            self.model = None

        # 按钮事件
        self.btn_open.clicked.connect(self.open_image)
        self.btn_detect.clicked.connect(self.detect_defects)
        self.status_bar.showMessage("就绪")

    def update_confidence_label(self, value):
        self.confidence = value / 100.0
        self.confidence_label.setText(f"置信度阈值: {self.confidence:.2f}")

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择金属表面图像",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*.*)"
        )
        if file_path:
            try:
                self.current_image = cv2.imread(file_path)
                if self.current_image is None:
                    try:
                        from PIL import Image
                        pil_image = Image.open(file_path)
                        self.current_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    except ImportError:
                        self.status_bar.showMessage("PIL未安装，无法读取此图像格式", 3000)
                        QMessageBox.warning(self, "图像格式不支持", "请安装Pillow库以支持更多图像格式")
                        return
                    except Exception as e:
                        self.status_bar.showMessage(f"图像读取错误: {str(e)}", 3000)
                        return

                if self.current_image is not None:
                    self.display_image(self.current_image, self.original_label)
                    self.btn_detect.setEnabled(True)
                    self.status_bar.showMessage(f"已加载图像: {file_path}", 3000)
                else:
                    QMessageBox.warning(self, "图像加载失败", "无法读取选择的图像文件")
            except Exception as e:
                QMessageBox.warning(self, "图像加载错误", f"读取图像时出错: {str(e)}")
                print(f"图像加载错误: {e}")

    def detect_defects(self):
        if self.current_image is not None and self.model is not None:
            self.btn_detect.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.status_bar.showMessage("正在检测缺陷...")
            QApplication.processEvents()
            self.detection_thread = DetectionThread(self.model, self.current_image, self.confidence)
            self.detection_thread.finished.connect(self.on_detection_finished)
            self.detection_thread.start()
        elif self.model is None:
            QMessageBox.warning(self, "模型未加载", "无法加载YOLOv8模型，请检查模型文件是否存在")
            self.btn_detect.setEnabled(True)

    def on_detection_finished(self, result_img):
        self.display_image(result_img, self.result_label)
        self.btn_detect.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("检测完成!", 3000)

    def display_image(self, image, label):
        try:
            if image is None or image.size == 0:
                print("显示图像错误: 空图像")
                return
            h, w, ch = image.shape
            bytes_per_line = ch * w
            q_img = QImage(image.data, w, h, bytes_per_line, QImage.Format_BGR888)
            if q_img.isNull():
                print("QImage创建失败")
                return
            pixmap = QPixmap.fromImage(q_img)
            if pixmap.isNull():
                print("QPixmap创建失败")
                return
            scaled_pixmap = pixmap.scaled(
                label.width(), label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"显示图像时出错: {e}")
            error_image = np.zeros((500, 500, 3), dtype=np.uint8)
            cv2.putText(error_image, f"显示错误: {str(e)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            self.display_image(error_image, label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MetalDefectDetector()
    window.show()
    sys.exit(app.exec())