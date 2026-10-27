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
    groups = [('6b78a7242772bdce641eedaeb6a03e3650ba4615', 'module_sg1', ['Sg1_Pipeline.py', 'old/', 'requirements.txt', 'README.md']),
              ('eccb03c43c4fc8450316e5e7a13e39fa084c029b', 'module_sg3', ['sg3/', 'tests/', 'run_sg3.py', 'requirements.txt', 'README.md']),
              ('c5bd34dc15974e5f3e1028d6b3a426939eeb9e22', 'module_sg4', ['sg4/', 'tests/', 'mock/', 'config/', 'replay.py', 'evaluate.py', 'sweep.py', 'requirements.txt', 'README.md'])]
    for ref, dest, prefixes in groups:
        files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', ref], cwd=ROOT, text=True).splitlines()
        for source in files:
            if '__pycache__' not in source and any(source == p or (p.endswith('/') and source.startswith(p)) for p in prefixes):
                copy(ref, source, f'{dest}/{source}')
    ref = '4cc9a2531bff7e8f35bf23786b8c1ce8d748a326'
    for name in ['decision_rules', 'weighted_fusion', 'compare_methods', 'mock_inputs']:
        copy(ref, f'module_sg5/{name}', f'module_sg5/{name}')
    for name in ['decision_rules', 'weighted_fusion']:
        copy(ref, f'module_sg5/{name}', f'module_sg5/{name}.py')
