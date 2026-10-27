"""Reproduce the audited path-preserving subgroup imports (no branch deletions)."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def copy(ref, source, target):
    data = subprocess.check_output(['git', 'show', f'{ref}:{source}'], cwd=ROOT)
    path = ROOT / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

if __name__ == '__main__':
    groups = [('origin/module_sg1', 'module_sg1', ['Sg1_Pipeline.py', 'old/', 'requirements.txt', 'README.md']),
              ('origin/module_sg3', 'module_sg3', ['sg3/', 'tests/', 'run_sg3.py', 'requirements.txt', 'README.md']),
              ('origin/module_sg4', 'module_sg4', ['sg4/', 'tests/', 'mock/', 'config/', 'replay.py', 'evaluate.py', 'sweep.py', 'requirements.txt', 'README.md'])]
    for ref, dest, prefixes in groups:
        files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', ref], cwd=ROOT, text=True).splitlines()
        for source in files:
            if '__pycache__' not in source and any(source == p or (p.endswith('/') and source.startswith(p)) for p in prefixes):
                copy(ref, source, f'{dest}/{source}')
    ref = 'origin/alveenashahidd-patch-1-1'
    for name in ['decision_rules', 'weighted_fusion', 'compare_methods', 'mock_inputs']:
        copy(ref, f'module_sg5/{name}', f'module_sg5/{name}')
    for name in ['decision_rules', 'weighted_fusion']:
        copy(ref, f'module_sg5/{name}', f'module_sg5/{name}.py')
