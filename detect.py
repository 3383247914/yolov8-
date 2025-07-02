from ultralytics import YOLO
import cv2
import glob


def detect_defects():
    # 加载训练好的模型
    model = YOLO('models/metal_defect_best.pt')

    # 处理测试图像
    test_images = glob.glob('data/test/*.jpg')  # 创建测试目录存放待检测图像

    for img_path in test_images:
        # 读取图像
        img = cv2.imread(img_path)

        # 运行检测
        results = model(img, conf=0.5)

        # 可视化结果
        annotated_img = results[0].plot()

        # 显示结果
        cv2.imshow('Detection Result', annotated_img)
        cv2.waitKey(0)

        # 保存结果
        output_path = img_path.replace('test', 'results')
        cv2.imwrite(output_path, annotated_img)

    cv2.destroyAllWindows()


if __name__ == '__main__':
    detect_defects()