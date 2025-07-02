from ultralytics import YOLO
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'  # 解决OpenMP冲突
import torch


def train_model():
    # 检查GPU是否可用
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"使用设备: {device}")

    # 数据集配置路径
    data_config = 'C:/Users/pc/Desktop/基于yolov8的金属检测模型/metal_defect/metal_defect.yaml'

    # 创建模型
    model = YOLO('yolov8n.pt')  # 使用预训练模型

    # 训练参数
    train_params = {
        'data': data_config,
        'epochs': 100,
        'imgsz': 640,
        'batch': 16,
        'name': 'metal_defect_v1',
        'save': True,
        'pretrained': True,
        'device': 0 if device == 'cuda' else 'cpu',  # 使用GPU
        'optimizer': 'AdamW',  # 更高效的优化器
        'lr0': 0.001,  # 初始学习率
        'cos_lr': True,  # 使用余弦退火学习率
        'augment': True,  # 启用数据增强
        'dropout': 0.1,  # 防止过拟合
        'patience': 50,  # 早停耐心值
        'workers': 4  # 数据加载线程数
    }

    # 开始训练
    results = model.train(**train_params)

    # 保存训练好的模型
    model.save('models/metal_defect_best.pt')
    print(f"训练完成! 模型已保存到 models/metal_defect_best.pt")


if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)
    train_model()