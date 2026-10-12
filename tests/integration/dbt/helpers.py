import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DBT_DIR = PROJECT_ROOT / "dbt"


def run_dbt(profiles_dir: Path, *args: str) -> None:
    subprocess.run(
        [
            "uv", "run", "dbt", *args,
            "--profiles-dir", str(profiles_dir),
        ],
        cwd=DBT_DIR,
        check=True,
    )