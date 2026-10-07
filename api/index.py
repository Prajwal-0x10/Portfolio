import sys
from pathlib import Path

# Add project root and src to sys.path so imports work properly in Vercel Serverless
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from portfolio.backend.main import app
