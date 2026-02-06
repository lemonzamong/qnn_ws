# 🚀 QNN 모델 변환 마스터 가이드 (DINOv3 기준)

## 0. 환경 설정 (공통)

모든 작업 전 반드시 실행해야 합니다.

```bash
cd ~/workspace/qnn_ws
source qnn_env/bin/activate
source qairt/2.43.0.260128/bin/envsetup.sh
export ANDROID_NDK_ROOT="$HOME/workspace/qnn_ws/android-ndk-r26c"
export PATH="${ANDROID_NDK_ROOT}:${PATH}"
export QNN_AARCH64_UBUNTU_GCC_94="/usr"
```

## 1. 전반부: 모델 에셋 생성 (Converter)

PyTorch에서 추출한 ONNX를 QNN용 소스(`cpp`)와 가중치(`bin`)로 바꿉니다.

| 모드 | 명령어 |
| --- | --- |
| **FP16** | `qnn-onnx-converter -i models/dinov3_vith16plus_eager.onnx -o models/dinov3_vith16plus_fp16.cpp --float_bitwidth 16` |
| **INT8** | `qnn-onnx-converter -i models/dinov3_vith16plus_eager.onnx -o models/dinov3_vith16plus_int8.cpp --input_list input_list.txt --weights_bitwidth 8 --bias_bitwidth 8 --act_bitwidth 8 --param_quantizer tf --act_quantizer tf` |

## 2. 중반부: 모델 라이브러리 빌드 (Generator)

생성된 `cpp`를 실제 실행 가능한 `.so` 파일로 컴파일합니다.

### **[Host용 - x86_64]** (바이너리 생성 도구용)

* **FP16:** `qnn-model-lib-generator -c models/dinov3_vith16plus_fp16.cpp -b models/dinov3_vith16plus_fp16.bin -t x86_64-linux-clang -o libs`
* **INT8:** `qnn-model-lib-generator -c models/dinov3_vith16plus_int8.cpp -b models/dinov3_vith16plus_int8.bin -t x86_64-linux-clang -o libs`

### **[Target용 - aarch64]** (IQ-9075 보드 배포용 - **Light 버전**)

* **FP16:** `qnn-model-lib-generator -c models/dinov3_vith16plus_fp16.cpp -b models/dinov3_vith16plus_fp16.bin -t aarch64-ubuntu-gcc9.4 -o libs`
* **INT8:** `qnn-model-lib-generator -c models/dinov3_vith16plus_int8.cpp -b models/dinov3_vith16plus_int8.bin -t aarch64-ubuntu-gcc9.4 -o libs`

(참고: `-b` 옵션은 `.bin` 파일이 필요할 때 사용합니다. 위 명령어에 포함시켰습니다.)

## 3. 후반부: 최적화 바이너리 생성 (Context Binary)

가장 중요한 단계로, NPU(HTP) 전용 실행 파일을 만듭니다.

### **[FP16 HTP 전용]**

```bash
qnn-context-binary-generator \
  --model libs/x86_64-linux-clang/libdinov3_vith16plus_fp16.so \
  --backend $QAIRT_SDK_ROOT/lib/x86_64-linux-clang/libQnnHtp.so \
  --output_dir final_binary/fp16 \
  --binary_file dinov3_fp16_htp.serialized \
  --config_file htp_config.json
```

### **[INT8 HTP 전용]**

```bash
qnn-context-binary-generator \
  --model libs/x86_64-linux-clang/libdinov3_vith16plus_int8.so \
  --backend $QAIRT_SDK_ROOT/lib/x86_64-linux-clang/libQnnHtp.so \
  --output_dir final_binary/int8 \
  --binary_file dinov3_int8_htp.serialized \
  --config_file htp_config.json
```

## 📂 최종 보드 배포 리스트 (IQ-9075)

보드 용량 절약을 위해 아래 파일들만 챙기시면 됩니다.

| 구분 | FP16 멤버 | INT8 멤버 |
| --- | --- | --- |
| **Model SO** | `libs/aarch64-ubuntu-gcc9.4/libdinov3_vith16plus_fp16.so` | `libs/aarch64-ubuntu-gcc9.4/libdinov3_vith16plus_int8.so` |
| **NPU Binary** | `final_binary/fp16/dinov3_fp16_htp.serialized.bin` | `final_binary/int8/dinov3_int8_htp.serialized.bin` |
| **QNN Libs** | `libQnnHtp.so`, `libQnnHtpV73Stub.so`, `libQnnSystem.so`, `libQnnHtpV73Skel.so` | (좌동) |

## 💡 INT8 사용 시 주의사항

1. **정확도 확인:** INT8은 속도는 압도적으로 빠르지만, DINOv3의 정교한 특징 추출 능력이 미세하게 떨어질 수 있습니다. `input_list.txt`에 모델이 학습 때 본 것과 유사한 양질의 데이터를 10~100장 정도 넣어 양자화하는 것이 좋습니다.
2. **Skel 파일:** IQ-9075는 **v73** 아키텍처이므로, SDK 내 `lib/hexagon-v73/unsigned/libQnnHtpV73Skel.so` 파일을 반드시 보드의 실행 경로에 함께 두어야 합니다.