import torch
print(torch.cuda.is_available())  # 应该输出True
print(torch.cuda.get_device_name(0))  # 应该显示你的RTX 4060