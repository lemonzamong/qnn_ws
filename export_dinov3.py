import torch
from transformers import AutoModel, AutoConfig
import os

model_name = "facebook/dinov3-vith16plus-pretrain-lvd1689m"
output_path = "dinov3_vith16plus_eager.pt"

def export_model():
    print(f"Loading {model_name} with eager attention and return_dict=False...")
    try:
        # Load config and set return_dict to False to ensure tuple output
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        config.return_dict = False
        
        # Load model using AutoModel with eager attention
        model = AutoModel.from_pretrained(
            model_name, 
            config=config,
            trust_remote_code=True,
            attn_implementation="eager" 
        )
        model.eval()
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Create dummy input matches 224x224 input
    input_shape = (1, 3, 224, 224)
    dummy_input = torch.randn(input_shape)

    print(f"Tracing model with input shape {input_shape}...")
    
    try:
        # Strict=False is often needed for HF models
        traced_model = torch.jit.trace(model, dummy_input, strict=False)
        print(f"Saving to {output_path}...")
        traced_model.save(output_path)
        print("Model exported successfully.")
    except Exception as e:
        print(f"Failed to trace model: {e}")

if __name__ == "__main__":
    export_model()
