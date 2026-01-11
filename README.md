
# 智能证件照批量处理工具 (Smart Crop Skill) 使用说明

这个脚本 (`smart_crop_skill.py`) 允许你在不打开任何窗口的情况下，批量自动裁剪和调整图片尺寸。

## 1. 准备工作

确保你已经安装了 Python 和必要的库：

```bash
pip install pillow
```

## 2. 基本用法

打开终端 (Terminal)，进入脚本所在的目录：
```bash
cd /Users/apple/Documents/照片处理
```

基本的运行命令格式如下：
```bash
python3 smart_crop_skill.py --input <输入文件夹路径> --output <输出文件夹路径> [参数]
```

## 3. 常用参数说明

- `--input` 或 `-i`: **(必须)** 原始图片所在的文件夹。
- `--output` 或 `-o`: **(必须)** 处理后图片保存的文件夹（会自动创建）。
- `--width`: 目标宽度（像素），默认 295。
- `--height`: 目标高度（像素），默认 413。
- `--dpi`: 图片分辨率，默认 300。
- `--format`: 输出格式，可选 `JPEG` (默认) 或 `PNG`。
- `--prefix`: 文件名前缀，默认 `processed_`。

## 4. 常见场景示例

### 示例 A：制作 1寸照片 (295x413) - 默认设置
```bash
python3 smart_crop_skill.py -i ./原图文件夹 -o ./一寸照输出
```

### 示例 B：制作 2寸照片 (413x579)
```bash
python3 smart_crop_skill.py -i ./原图文件夹 -o ./二寸照输出 --width 413 --height 579
```

### 示例 C：制作身份证/驾驶证照片 (358x441) 并保存为 PNG
```bash
python3 smart_crop_skill.py -i ./原图文件夹 -o ./证件照输出 --width 358 --height 441 --format PNG
```

### 示例 D：自定义前缀
如果你想让文件名前面加上 "ID_"：
```bash
python3 smart_crop_skill.py -i ./input -o ./output --prefix "ID_"
```

## 5. 尺寸参考表

| 类型 | 宽 (px) | 高 (px) | 备注 (300 DPI) |
| :--- | :--- | :--- | :--- |
| **1寸** | 295 | 413 | 常用于简历、证件 |
| **小2寸** | 413 | 531 | 公务员考试等 |
| **2寸** | 413 | 579 | 护照、签证常用 |
| **身份证** | 358 | 441 | 居民身份证、驾照 |
| **大1寸** | 390 | 567 | 护照 |
