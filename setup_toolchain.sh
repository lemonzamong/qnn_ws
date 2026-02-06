#!/bin/bash

# Define Toolchain Path
TOOLCHAIN_DIR="$(pwd)/toolchain_11"
USR_BIN="$TOOLCHAIN_DIR/usr/bin"

echo "🔧 Setting up custom toolchain for GCC 11..."

# 1. Install GCC 11 if missing (requires sudo)
if ! command -v aarch64-linux-gnu-g++-11 &> /dev/null; then
    echo "⚠️  GCC 11 Cross-Compiler not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y g++-11-aarch64-linux-gnu gcc-11-aarch64-linux-gnu
else
    echo "✅ GCC 11 Cross-Compiler found."
fi

# 2. Create Directory Structure
echo "📂 Creating '$USR_BIN'..."
mkdir -p "$USR_BIN"

# 3. Create Symlinks (The Trick)
# Link GCC 11 specific binaries to standard names
ln -sf /usr/bin/aarch64-linux-gnu-g++-11 "$USR_BIN/aarch64-linux-gnu-g++"
ln -sf /usr/bin/aarch64-linux-gnu-gcc-11 "$USR_BIN/aarch64-linux-gnu-gcc"

# Link other necessary tools (ar, ld, objcopy, etc.) from system default
# We iterate over common tools and link them if they exist
TOOLS="ar as ld objcopy objdump ranlib strip nm"
for tool in $TOOLS; do
    SYS_TOOL="/usr/bin/aarch64-linux-gnu-$tool"
    if [ -f "$SYS_TOOL" ]; then
        ln -sf "$SYS_TOOL" "$USR_BIN/aarch64-linux-gnu-$tool"
        echo "   🔗 Linked $tool"
    else
        echo "   ⚠️  Warning: $SYS_TOOL not found."
    fi
done

echo ""
echo "🎉 Toolchain setup complete!"
echo "👉 To use this, run:"
echo "   export QNN_AARCH64_UBUNTU_GCC_94=\"$TOOLCHAIN_DIR\""
