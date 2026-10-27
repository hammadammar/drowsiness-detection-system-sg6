#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3 -m embedded_sg6.audit > jetson_environment_before_setup.json
python3 - <<'PY'
import sys, platform
print('Detected:', platform.platform(), platform.machine(), sys.version)
if sys.version_info < (3,10):
    raise SystemExit('STOP: subgroup code requires Python >=3.10. Older Nano/JetPack Python cannot run this unchanged. Review START_HERE_JETSON.md; do not replace system Python/CUDA.')
PY
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install 'PyYAML>=6' 'jsonschema>=4.18' 'psutil>=5.9' 'pytest>=7'
.venv/bin/python - <<'PY'
import importlib.util
for name in ('numpy','cv2','mediapipe','pandas'):
    print(name, 'available' if importlib.util.find_spec(name) else 'MISSING: install a verified wheel/build compatible with this board and Python')
PY
echo 'Core setup complete. Read START_HERE_JETSON.md before installing camera/inference dependencies.'
