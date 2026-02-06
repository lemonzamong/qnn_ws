# DINOv3 QNN Conversion & Deployment Project

This repository documents the complete pipeline for converting the `facebook/dinov3-vith16plus-pretrain-lvd1689m` model for deployment on Qualcomm AI Engine, specifically targeting the **IQ-9075 (QCS9075)** device with HTP v73 architecture.

## 🏗️ Project Architecture & Pipeline

The value chain from PyTorch to Edge Device is as follows:

```mermaid
graph TD
    A[PyTorch Model (HF)] -->|Export & Fix| B(ONNX Model)
    B -->|Bypass 2GB Limit| C{External Data ONNX}
    C -->|qnn-onnx-converter| D[QNN C++/BIN Assets]
    
    subgraph "Host (x86_64) Processing"
        D -->|Compile (GCC/Clang)| E[Host .so Library]
        E -->|qnn-context-binary-generator| F[HTP Context Binary (.serialized)]
    end
    
    subgraph "Target (QCS9075) Processing"
        D -->|Compile (GCC 11.2)| G[Target .so Library]
    end
    
    F -->|Deploy| H[Target Device (IQ-9075)]
    G -->|Deploy| H
    I[QNN Libs (System, Htp, Skel, etc)] -->|Deploy| H
```

### Key Artifacts
- **Model Inputs:** `dinov3_vith16plus_eager.onnx` (FP32)
- **Intermediate:** `libs/libdinov3_vith16plus_int8.so` (Model Library)
- **Final Output:** `final_binary/dinov3_int8_htp.serialized.bin` (Optimized Context Binary)

---

## 🛠️ Environment Setup

### 1. Prerequisites
- **OS:** Linux (Ubuntu 20.04/22.04 recommended)
- **SDK:** Qualcomm AI Stack (QNN SDK) v2.43+
- **Compiler:** 
  - Host: `clang` (for simulation/context generation)
  - Target: `g++-11-aarch64-linux-gnu` (Specific version required for HTP v73 compatibility)

### 2. Environment Variables
Setup your shell environment before running any commands:
```bash
cd ~/workspace/qnn_ws
source qnn_env/bin/activate  # Python venv
source qairt/2.43.0.260128/bin/envsetup.sh
export PATH="${PATH}:/usr/bin"
# Critical for Cross-Compilation
export QNN_AARCH64_UBUNTU_GCC_94="/home/hyeokjun/workspace/qnn_ws/toolchain_11" 
```

> **Note:** We use a custom `toolchain_11` directory to force QNN to use GCC 11.2 instead of the system default (often GCC 13) or the older SDK default (GCC 9.4), ensuring compatibility with the device's HTP v73 library requirements.

---

## 🚀 Step-by-Step Implementation Guide

### Phase 1: ONNX Export (Handling Large Weights)
Standard export fails due to Protobuf's 2GB limit. We implemented a workaround using external data format:
```bash
python export_onnx.py
# Generates: dinov3_vith16plus_eager.onnx + .onnx_data
```

### Phase 2: QNN Conversion (FP16 / INT8)
We use `qnn-onnx-converter` to generate the network structure (`.cpp`) and weights (`.bin`).

**INT8 Quantization (with Calibration):**
Includes a calibration step using `42dot_dataset` to minimize accuracy loss.
```bash
qnn-onnx-converter \
  -i models/dinov3_vith16plus_eager.onnx \
  -o models/dinov3_vith16plus_int8.cpp \
  --input_list input_list.txt \
  --weights_bitwidth 8 \
  --bias_bitwidth 8 \
  --act_bitwidth 8
```

### Phase 3: Model Library Compilation
We compile the `.cpp` model definition into a shared library (`.so`). 

**Target Compilation (QCS9075):**
Uses our custom GCC 11 toolchain setup.
```bash
qnn-model-lib-generator \
  -c models/dinov3_vith16plus_int8.cpp \
  -b models/dinov3_vith16plus_int8.bin \
  -t aarch64-ubuntu-gcc9.4 \
  -o libs
```
*Output:* `libs/aarch64-ubuntu-gcc9.4/libdinov3_vith16plus_int8.so`

### Phase 4: HTP Context Binary Generation
Generates the highly optimized binary for the Hexagon NPU.
```bash
qnn-context-binary-generator \
  --model libs/x86_64-linux-clang/libdinov3_vith16plus_int8.so \
  --backend libQnnHtp.so \
  --output_dir final_binary/int8 \
  --binary_file dinov3_int8_htp.serialized \
  --config_file htp_config.json
```
*Output:* `final_binary/int8/dinov3_int8_htp.serialized.bin`

---

## 🔧 Troubleshooting & Solved Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Protobuf Limit** | Model > 2GB fails standard export | Used `save_as_external_data=True` in PyTorch export script. |
| **Missing .cpp source** | `qairt-converter` produces binaries named .cpp | Switched to `qnn-onnx-converter` which strictly produces source/bin pairs. |
| **Compiler Error (objcopy)** | Missing binutils in cross-compile env | Symlinked full `binutils-aarch64-linux-gnu` suite to custom toolchain dir. |
| **Library Mismatch** | Target board uses older glibc/sdk than host GCC | **Critical:** Forced usage of `g++-11` by aliasing it in `toolchain_11/` directory. |
| **Missing SSH Key** | User config pointed to non-existent key | Switched to `sshpass` for password-based automation. |

---

## 📲 Deployment (IQ-9075)

The deployment package has been successfully transferred to the target device.

### Target Location
- **IP:** `100.89.129.28`
- **Path:** `~/Workspace/inference/`
- **User:** `ubuntu` / `alfoehwjs`

### Deployment Content
1. **Model Library:** `libdinov3_vith16plus_int8.so` (800MB+)
2. **Context Binary:** `dinov3_int8_htp.serialized.bin` (optimized runtime)
3. **QNN Runtime Libs:** 
   - `libQnnHtp.so`
   - `libQnnHtpV73Skel.so` (Critical for v73 architecture)
   - `libQnnSystem.so`
   - `libQnnHtpV73Stub.so`

### Verification Command
```bash
sshpass -p alfoehwjs ssh IQ9075 "ls -lh ~/Workspace/inference/"
```
