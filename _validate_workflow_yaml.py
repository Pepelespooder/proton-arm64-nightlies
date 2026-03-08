from pathlib import Path
import yaml
path = Path('/mnt/c/Users/Makin/Desktop/Proton build/proton-arm64-nightlies/.github/workflows/proton-nightly-build.yml')
obj = yaml.safe_load(path.read_text(encoding='utf-8'))
print('loaded:', type(obj).__name__)
print('release_steps:', len(obj['jobs']['release']['steps']))
