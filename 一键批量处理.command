#!/bin/bash

# 获取脚本所在目录
cd "$(dirname "$0")"

# 设置颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 智能证件照批量处理工具 (Smart Crop Skill) ===${NC}"
echo ""

# 检查输入文件夹
if [ ! -d "input_images" ]; then
    echo "创建输入文件夹: input_images"
    mkdir -p input_images
    echo -e "${GREEN}✓ 文件夹已创建${NC}"
    echo "请将需要处理的图片放入 'input_images' 文件夹中，然后重新运行此脚本。"
    open "input_images"
    read -p "按回车键退出..."
    exit
fi

# 检查输出文件夹
if [ ! -d "output_images" ]; then
    mkdir -p "output_images"
fi

# 计算输入文件数量
count=$(ls input_images/*.{jpg,jpeg,png,bmp,tiff,webp} 2>/dev/null | wc -l)
if [ "$count" -eq "0" ]; then
    echo "警告: 'input_images' 文件夹是空的。"
    echo "请放入图片后重试。"
    open "input_images"
    read -p "按回车键退出..."
    exit
fi

echo "发现 $count 张图片待处理。"
echo ""
echo "请选择处理模式:"
echo "1) 1寸 (295x413, 300dpi)"
echo "2) 2寸 (413x579, 300dpi)"
echo "3) 身份证 (358x441, 300dpi)"
echo "4) 自定义尺寸"
echo ""
read -p "请输入选项 (1-4) [默认1]: " choice

# 默认选项
choice=${choice:-1}

width=295
height=413
prefix="processed_"

case $choice in
    1)
        width=295
        height=413
        prefix="1inch_"
        echo -e "${GREEN}>> 已选择: 1寸照片${NC}"
        ;;
    2)
        width=413
        height=579
        prefix="2inch_"
        echo -e "${GREEN}>> 已选择: 2寸照片${NC}"
        ;;
    3)
        width=358
        height=441
        prefix="ID_"
        echo -e "${GREEN}>> 已选择: 身份证照片${NC}"
        ;;
    4)
        read -p "请输入宽度 (px): " width
        read -p "请输入高度 (px): " height
        prefix="custom_"
        echo -e "${GREEN}>> 已选择: 自定义 ${width}x${height}${NC}"
        ;;
    *)
        echo "无效选项，使用默认 (1寸)"
        ;;
esac

echo ""
echo "正在处理中，请稍候..."
echo "----------------------------------------"

# 运行 Python 脚本
python3 smart_crop_skill.py \
    --input "./input_images" \
    --output "./output_images" \
    --width "$width" \
    --height "$height" \
    --prefix "$prefix"

echo "----------------------------------------"
echo -e "${GREEN}处理完成!${NC}"
echo "结果保存在: output_images"

# 打开输出文件夹
open "output_images"

# 防止窗口立即关闭
read -p "按回车键退出..."
