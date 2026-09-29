#!/usr/bin/env bash
# Downloads the offline TTS assets (not committed to git): Kokoro model + voices, and espeak-ng (from the Piper bundle).
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p assets; cd assets
[ -f kokoro.onnx ] || curl -sSL -o kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f voices.bin ]  || curl -sSL -o voices.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
if [ ! -d piper ]; then
  curl -sSL -o piper.tgz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
  tar xzf piper.tgz && rm piper.tgz && chmod +x piper/espeak-ng
fi
python3 -c "import onnxruntime, numpy" || pip install onnxruntime numpy --break-system-packages
echo "assets ready"
