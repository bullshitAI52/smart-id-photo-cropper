
import os
import sys
import shutil
from PIL import Image
from smart_crop_skill import SmartCropSkill

def test_skill():
    # Setup test directories
    input_dir = "./test_input"
    output_dir = "./test_output"
    
    if os.path.exists(input_dir):
        shutil.rmtree(input_dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    os.makedirs(input_dir)
    os.makedirs(output_dir)
    
    # Create valid dummy image (Red square)
    img_path = os.path.join(input_dir, "test_img.jpg")
    img = Image.new('RGB', (1000, 1000), color = 'red')
    img.save(img_path)
    
    # Run Skill
    print("Running SmartCropSkill...")
    skill = SmartCropSkill(input_dir, output_dir, config={'target_width': 100, 'target_height': 100})
    skill.run()
    
    # Verify output
    expected_output = os.path.join(output_dir, "processed_test_img.jpg")
    if os.path.exists(expected_output):
        out_img = Image.open(expected_output)
        print(f"Output image found: {expected_output}")
        print(f"Dimensions: {out_img.size}")
        if out_img.size == (100, 100):
            print("TEST PASSED: Image processed and resized correctly.")
        else:
            print(f"TEST FAILED: Incorrect dimensions {out_img.size} != (100, 100)")
    else:
        print(f"TEST FAILED: Output file not found at {expected_output}")

    # Clean up
    # shutil.rmtree(input_dir)
    # shutil.rmtree(output_dir)

if __name__ == "__main__":
    test_skill()
