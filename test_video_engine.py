"""
Static smoke test for the engine.

This test only verifies Python syntax/import structure.
It does not call fal.ai.
"""

import ast
from pathlib import Path

path = Path(__file__).parents[1] / "backend" / "engines" / "video_generation_engine.py"
ast.parse(path.read_text(encoding="utf-8"))
print("VIDEO GENERATING ENGINE SYNTAX OK")
