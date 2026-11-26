import sys
from pathlib import Path

# The app is run with api/ as its module root (`from config import settings`),
# so tests need api/ on sys.path too.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
