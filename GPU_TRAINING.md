# 双扣AI GPU训练指南

## 1. 上传代码到服务器

将以下文件上传到GPU服务器：
- `game/` 文件夹（游戏引擎）
- `train_gpu.py`（训练脚本）

## 2. 安装依赖

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install numpy
```

## 3. 运行训练

### 快速测试 (100局)
```bash
python train_gpu.py --games 100 --epochs 10 --batch 32
```

### 标准训练 (1000局)
```bash
python train_gpu.py --games 1000 --epochs 30 --batch 64
```

### 深度训练 (5000局)
```bash
python train_gpu.py --games 5000 --epochs 50 --batch 128
```

## 4. 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--games` | 1000 | 自我对弈局数 |
| `--epochs` | 30 | 训练轮数 |
| `--batch` | 64 | 批次大小 |
| `--lr` | 0.001 | 学习率 |
| `--model` | models/dl_ai.pt | 模型保存路径 |
| `--load` | None | 加载已有模型 |

## 5. 预期时间

| 规模 | GPU | 时间 | 费用(约) |
|------|-----|------|----------|
| 100局 | T4 | 2分钟 | ¥0.3 |
| 1000局 | T4 | 15分钟 | ¥2 |
| 5000局 | T4 | 1小时 | ¥7 |

## 6. 下载模型

训练完成后，下载 `models/dl_ai.pt` 到本地使用。

## 常用命令

```bash
# 查看GPU
nvidia-smi

# 测试PyTorch GPU
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 后台运行训练
nohup python train_gpu.py --games 1000 > train.log 2>&1 &

# 查看训练进度
tail -f train.log
```
