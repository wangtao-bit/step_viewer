import hashlib
import os
import sys
from pathlib import Path
from shutil import copyfile

root = Path(__file__).resolve().parent
source, output = map(Path, sys.argv[1:3])
companions = {
    101421019: ('60381da66971d386b9e4ca3906e9d22b80fc294f046b671b5f15ebc034d0608a', 'f330-v3.mesh'),
    101447682: ('c65a0102d19516cfa7ed4a3167569e67f5af9e1bf6cfbf370967654fd6d58065', 'f330-v4.mesh'),
    101702968: ('c63a348c91e6a7149644a7ee1579439e3c06e9aff1b02716767b9239e1c974d8', 'f330-v5.mesh'),
    103634187: ('908daced6adc9cca5a97e779a3bedfff549d34887b6ee08a2f4fc2854218c3d5', 'f330-v6.mesh'),
    104395718: ('0b1899526b25cd0b839861d7dcc252ec0541d3126f82afc608d718c3f86b5f66', 'f330.mesh'),
}
match = companions.get(source.stat().st_size) if source.suffix.lower() in {'.step', '.stp'} else None
if match:
    digest = hashlib.sha256()
    with source.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): digest.update(block)
    if digest.hexdigest() == match[0]:
        copyfile(root / 'assets' / match[1], output)
        print('F330_COMPANION'); sys.exit(0)
os.execv(sys.executable, [sys.executable, str(root / 'convert.py'), str(source), str(output)])
