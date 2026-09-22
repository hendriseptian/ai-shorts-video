import ast
from pathlib import Path

path = (
    Path(__file__).parent
    / "backend"
    / "engines"
    / "image_storage_engine.py"
)

ast.parse(path.read_text(encoding="utf-8"))
print("IMAGE STORAGE ENGINE SYNTAX OK")
