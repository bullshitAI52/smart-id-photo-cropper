#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Crop Skill - Headless Batch Image Processing
Extracted from SmartBatchCropApp
"""

import os
import argparse
from PIL import Image

class SmartCropSkill:
    def __init__(self, input_dir, output_dir, config=None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Default configuration
        self.config = {
            'target_width': 295,
            'target_height': 413,
            'target_dpi': 300,
            'horizontal_center': True,
            'vertical_center': False,
            'format': 'JPEG',
            'name_prefix': 'processed_',
            'skip_errors': True
        }
        
        if config:
            self.config.update(config)

        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def calculate_crop_rect(self, pil_image, target_width, target_height, horizontal_center, vertical_center):
        """Calculate the crop rectangle based on target size and centering options."""
        img_width, img_height = pil_image.size

        # Calculate target and image aspect ratios
        target_ratio = target_width / target_height
        img_ratio = img_width / img_height

        # Calculate crop dimensions
        if abs(img_ratio - target_ratio) < 0.01:
            # Same aspect ratio, just scale
            scale_w = target_width / img_width
            scale_h = target_height / img_height
            scale = min(scale_w, scale_h)
            crop_width = int(target_width / scale)
            crop_height = int(target_height / scale)
        elif img_ratio > target_ratio:
            # Image is wider, crop width
            crop_height = img_height
            crop_width = int(crop_height * target_ratio)
            if crop_width > img_width:
                crop_width = img_width
                crop_height = int(crop_width / target_ratio)
        else:
            # Image is taller, crop height
            crop_width = img_width
            crop_height = int(crop_width / target_ratio)
            if crop_height > img_height:
                crop_height = img_height
                crop_width = int(crop_height * target_ratio)

        # Apply centering
        if horizontal_center:
            x1 = max(0, (img_width - crop_width) // 2)
        else:
            x1 = 0

        if vertical_center:
            y1 = max(0, (img_height - crop_height) // 2)
        else:
            y1 = 0

        x2 = x1 + crop_width
        y2 = y1 + crop_height

        # Ensure crop rect is within image bounds
        if x2 > img_width:
            x1 = img_width - crop_width
            x2 = img_width

        if y2 > img_height:
            y1 = img_height - crop_height
            y2 = img_height

        return (int(x1), int(y1), int(x2), int(y2))

    def process_image(self, input_path, output_path):
        """Process a single image: open, crop, resize, and save."""
        try:
            pil_image = Image.open(input_path)

            crop_rect = self.calculate_crop_rect(
                pil_image,
                self.config['target_width'],
                self.config['target_height'],
                self.config['horizontal_center'],
                self.config['vertical_center']
            )

            # Crop and resize
            cropped = pil_image.crop(crop_rect)
            target_size = (self.config['target_width'], self.config['target_height'])

            if cropped.size != target_size:
                cropped = cropped.resize(target_size, Image.Resampling.LANCZOS)

            # Set DPI and save
            dpi = self.config['target_dpi']
            cropped.info['dpi'] = (dpi, dpi)

            fmt = self.config['format'].upper()
            if fmt == 'JPEG':
                 # JPEG doesn't support transparency, convert to RGB if needed
                if cropped.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', cropped.size, (255, 255, 255))
                    background.paste(cropped, mask=cropped.split()[-1])
                    cropped = background
                cropped.save(output_path, 'JPEG', quality=95, dpi=(dpi, dpi))
            elif fmt == 'PNG':
                cropped.save(output_path, 'PNG', dpi=(dpi, dpi))
            else:
                # Fallback or other formats
                cropped.save(output_path, dpi=(dpi, dpi))

            return True

        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False

    def run(self):
        """Run batch processing."""
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp')
        files = [f for f in os.listdir(self.input_dir) if f.lower().endswith(supported_formats)]
        
        print(f"Found {len(files)} images in {self.input_dir}")
        
        success_count = 0
        for i, filename in enumerate(files):
            input_path = os.path.join(self.input_dir, filename)
            
            # Construct output filename
            name_part, ext = os.path.splitext(filename)
            new_name = f"{self.config['name_prefix']}{name_part}"
            if self.config['format'].upper() == 'JPEG':
                new_name += ".jpg"
            elif self.config['format'].upper() == 'PNG':
                new_name += ".png"
            else:
                new_name += ext
                
            output_path = os.path.join(self.output_dir, new_name)

            if self.process_image(input_path, output_path):
                success_count += 1
                print(f"[{i+1}/{len(files)}] Processed: {filename} -> {new_name}")
            else:
                print(f"[{i+1}/{len(files)}] Failed: {filename}")
                if not self.config['skip_errors']:
                    break
        
        print(f"Batch processing complete. {success_count}/{len(files)} successful.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Crop Skill - Batch Image Processor")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing images")
    parser.add_argument("--output", "-o", required=True, help="Output directory for processed images")
    parser.add_argument("--width", type=int, default=295, help="Target width (default: 295)")
    parser.add_argument("--height", type=int, default=413, help="Target height (default: 413)")
    parser.add_argument("--dpi", type=int, default=300, help="Target DPI (default: 300)")
    parser.add_argument("--format", default="JPEG", choices=["JPEG", "PNG"], help="Output format")
    parser.add_argument("--prefix", default="processed_", help="Output filename prefix")
    
    args = parser.parse_args()
    
    config = {
        'target_width': args.width,
        'target_height': args.height,
        'target_dpi': args.dpi,
        'format': args.format,
        'name_prefix': args.prefix
    }
    
    skill = SmartCropSkill(args.input, args.output, config)
    skill.run()
