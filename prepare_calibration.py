import os
import glob
import numpy as np
from PIL import Image

def prepare_calibration_data(
    dataset_root="42dot_dataset",
    output_dir="calibration_data",
    num_samples=50,
    input_size=(224, 224)
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Find images
    print(f"Searching for images in {dataset_root}...")
    images = glob.glob(os.path.join(dataset_root, "**", "*.jpg"), recursive=True)
    if not images:
        print("No .jpg files found!")
        return
    
    selected_images = images[:num_samples]
    print(f"Selected {len(selected_images)} images for calibration.")
    
    # ImageNet stats
    mean = np.array([0.485, 0.456, 0.406]).astype(np.float32)
    std = np.array([0.229, 0.224, 0.225]).astype(np.float32)
    
    file_paths = []
    
    for i, img_path in enumerate(selected_images):
        try:
            # Load and preprocess
            img = Image.open(img_path).convert('RGB')
            img = img.resize(input_size, Image.Resampling.BILINEAR)
            img_data = np.array(img).astype(np.float32) / 255.0
            
            # Normalize and transpose (HWC -> CHW)
            # img_data = (img_data - mean) / std  # Ensure broadcasting works
            # Actually simplest way:
            img_data = (img_data - mean) / std
            
            # Transpose to CHW (PyTorch default)
            img_data = img_data.transpose(2, 0, 1)
            
            # Add batch dimension (1, 3, 224, 224)
            img_data = np.expand_dims(img_data, axis=0)
            
            # Save as raw
            raw_filename = f"calib_{i}.raw"
            raw_path = os.path.join(output_dir, raw_filename)
            img_data.tofile(raw_path)
            
            file_paths.append(os.path.abspath(raw_path))
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    # Write input_list.txt
    # Format: input_name:=/path/to/raw
    # Note: Input name is "pixel_values" based on our export script/ONNX inspection
    input_list_path = "input_list.txt"
    with open(input_list_path, "w") as f:
        for path in file_paths:
            f.write(f"pixel_values:={path}\n")
            
    print(f"Generated {len(file_paths)} calibration files.")
    print(f"Input list saved to {input_list_path}")

if __name__ == "__main__":
    prepare_calibration_data()
