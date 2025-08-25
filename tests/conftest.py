import os
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH for imports like `import app`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

