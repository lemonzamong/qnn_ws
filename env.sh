#!/bin/bash

# 1. Activate Python Environment
if [ -f "qnn_env/bin/activate" ]; then
    source qnn_env/bin/activate
    echo "✅ Python Venv Activated"
else
    echo "⚠️  Python Venv not found at qnn_env/bin/activate"
fi

# 2. Setup QNN/QAIRT SDK
# Adjust this path if your SDK version changes
SDK_ROOT="qairt/2.43.0.260128"
if [ -f "$SDK_ROOT/bin/envsetup.sh" ]; then
    source "$SDK_ROOT/bin/envsetup.sh"
    echo "✅ QNN SDK Environment Setup"
else
    echo "⚠️  QNN SDK not found at $SDK_ROOT"
fi

# 3. Setup Android NDK (If needed)
export ANDROID_NDK_ROOT="$HOME/workspace/qnn_ws/android-ndk-r26c"
export PATH="${ANDROID_NDK_ROOT}:${PATH}"

# 4. Setup Custom GCC 11 Toolchain (The Critical Step)
export QNN_AARCH64_UBUNTU_GCC_94="$(pwd)/toolchain_11"
echo "✅ Custom Toolchain Configured: $QNN_AARCH64_UBUNTU_GCC_94"

echo ""
echo "🚀 Environment Ready! You can now run converters and generators."
