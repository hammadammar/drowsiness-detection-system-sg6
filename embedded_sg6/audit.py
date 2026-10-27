"""Read-only host and optional Jetson diagnostics; never changes clocks or power."""
import importlib
try:
    import importlib.metadata as metadata
except ImportError:
    metadata = None
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

def command(argv):
    if not shutil.which(argv[0]):
        return {'status': 'UNAVAILABLE'}
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        return dict(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except Exception as exc:
        return {'error': str(exc)}

def audit():
    result = dict(platform=platform.platform(), architecture=platform.machine(), python=sys.version,
                  jetson=False, packages={}, files={}, commands={})
    for name in ('/proc/device-tree/model', '/etc/nv_tegra_release', '/etc/os-release', '/proc/meminfo'):
        path = Path(name)
        if path.is_file():
            result['files'][name] = path.read_text(errors='replace').replace('\x00','')
    result['jetson'] = '/etc/nv_tegra_release' in result['files']
    for name in ('numpy','cv2','mediapipe','torch','tensorrt','onnxruntime','psutil','yaml','jsonschema'):
        try:
            mod = importlib.import_module(name)
            result['packages'][name] = metadata.version(name) if name == 'jsonschema' and metadata else getattr(mod,'__version__','installed')
            if name == 'cv2':
                result['opencv_build'] = mod.getBuildInformation()
            if name == 'torch':
                result['torch_cuda'] = dict(available=mod.cuda.is_available(), version=mod.version.cuda, cudnn=mod.backends.cudnn.version())
            if name == 'psutil':
                result['memory'] = mod.virtual_memory()._asdict()
                result['swap'] = mod.swap_memory()._asdict()
                try:
                    result['cpu_count'] = mod.cpu_count()
                except Exception as exc:
                    result['cpu_count_error'] = str(exc)
        except Exception as exc:
            result['packages'][name] = f'UNAVAILABLE: {exc}'
    for argv in (['uname','-a'],['nvcc','--version'],['nvpmodel','-q'],['v4l2-ctl','--list-devices']):
        result['commands'][' '.join(argv)] = command(argv)
    result['utilities'] = {n:shutil.which(n) for n in ('tegrastats','jetson_clocks','nvpmodel','nvidia-smi','v4l2-ctl','gst-launch-1.0','nvcc')}
    result['linux_video_devices'] = [str(p) for p in Path('/dev').glob('video*')] if Path('/dev').exists() else None
    result['disk'] = shutil.disk_usage(Path.cwd())._asdict()
    return result

if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
