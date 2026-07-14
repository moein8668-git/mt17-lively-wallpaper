import sys
from pathlib import Path


PRESET_MANAGER_DIR = Path(__file__).resolve().parents[1] / "preset-manager"
sys.path.insert(0, str(PRESET_MANAGER_DIR))
