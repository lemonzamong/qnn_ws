import torch
import onnx
import os
import shutil

traced_path = "dinov3_vith16plus_eager.pt"
final_onnx_path = "dinov3_vith16plus_eager.onnx"
data_path = "dinov3_vith16plus_eager.onnx_data"

def export_onnx():
    print(f"Loading {traced_path}...")
    model = torch.jit.load(traced_path)
    model.eval()
    
    input_shape = (1, 3, 224, 224)
    dummy_input = torch.randn(input_shape)
    
    # Strategy: Export to temp dir (scattered), then rebundle
    temp_dir = "onnx_temp_export"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    temp_onnx = os.path.join(temp_dir, "model.onnx")
    
    print(f"1. Exporting scattered model to {temp_dir}...")
    try:
        torch.onnx.export(
            model,
            dummy_input,
            temp_onnx,
            input_names=["pixel_values"],
            output_names=["last_hidden_state"],
            opset_version=18,
            do_constant_folding=True
        )
        print("Scattered export successful.")
    except Exception as e:
        print(f"Export failed: {e}")
        return

    print("2. Bundling files...")
    try:
        model_proto = onnx.load(temp_onnx)
        
        print(f"Saving to {final_onnx_path} with single external data file...")
        onnx.save_model(
            model_proto,
            final_onnx_path,
            save_as_external_data=True,
            all_tensors_to_one_file=True,
            location=data_path,
            size_threshold=1024,
            convert_attribute=False
        )
        print(f"Success! Created {final_onnx_path} and {data_path}")
    except Exception as e:
        print(f"Bundling failed: {e}")
    finally:
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    export_onnx()
