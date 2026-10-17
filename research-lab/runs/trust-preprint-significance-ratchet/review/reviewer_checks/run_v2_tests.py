"""Run code/test_extract_v2.py's test functions without pytest (the venv has none)."""
import importlib.util, sys, traceback
from pathlib import Path
code = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(code))
spec = importlib.util.spec_from_file_location("t", code / "test_extract_v2.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = bad = 0
for name in dir(m):
    if name.startswith("test_"):
        try:
            getattr(m, name)(); print("PASS", name); ok += 1
        except Exception:
            print("FAIL", name); traceback.print_exc(); bad += 1
print(f"{ok} passed, {bad} failed")
