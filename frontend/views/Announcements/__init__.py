# runs before any submodules like AnnouncementStudent
from pathlib import Path
import sys, types, importlib.util

HERE = Path(__file__).resolve().parent

# expose ./db as top-level "db"
DB_DIR = HERE / "db"
if DB_DIR.exists():
    if "db" not in sys.modules:
        pkg = types.ModuleType("db")
        pkg.__path__ = [str(DB_DIR)]
        sys.modules["db"] = pkg
    if str(DB_DIR) not in sys.path:
        sys.path.insert(0, str(DB_DIR))

# make local Approval importable by absolute name too
def _ensure_local_mod(mod_name: str, file_name: str) -> None:
    if mod_name in sys.modules:
        return
    p = HERE / file_name
    if p.exists():
        spec = importlib.util.spec_from_file_location(mod_name, str(p))
        m = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(m)  # type: ignore
        sys.modules[mod_name] = m

_ensure_local_mod("AnnouncementAdminApproval", "AnnouncementAdminApproval.py")
