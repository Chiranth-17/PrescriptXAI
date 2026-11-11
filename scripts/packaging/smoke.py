"""Install the release wheel outside the checkout and exercise its installed entrypoints."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import venv
from pathlib import Path

CHECK = """
import importlib.metadata
import json
from pathlib import Path
import prescriptxai
from prescriptxai.workspace import initialize_workspace
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.adapters.registry import MachineRegistry
package = Path(prescriptxai.__file__).resolve()
assert package.is_relative_to(Path.cwd() / 'environment'), package
identity = json.loads((package.parent / '_build_info.json').read_text())
assert identity['git_commit'] and identity['tracked_source_dirty'] is False
assert importlib.metadata.version('prescriptxai') == prescriptxai.__version__
initialize_workspace(Path('.'))
config = load_config(Path('configs/default.yaml'))
assert config.tau_safe == 0.2 and config.tau_danger == 0.8
assert load_taxonomy(config.pipeline.taxonomy_path).controllable_feature_names()
assert MachineRegistry().get('cmapss_fd001').limits_status == 'demonstration'
print(json.dumps({'passed': True, 'version': prescriptxai.__version__, 'build': identity}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    uv = shutil.which("uv")
    if uv is None:
        raise FileNotFoundError("Install uv before running the packaging smoke test")
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="prescriptxai-wheel-") as name:
        root = Path(name)
        venv.create(root / "environment", system_site_packages=True, with_pip=False)
        python = root / "environment" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--no-deps",
                "--reinstall-package",
                "prescriptxai",
                str(wheel),
            ],
            cwd=root,
            env=environment,
            check=True,
        )
        result = subprocess.run(
            [str(python), "-c", CHECK],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [str(python), "-m", "prescriptxai.cli", "--help"],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        receipt = json.loads(result.stdout)
        receipt["dependencies"] = (
            "Inherited installed dependencies; wheel import and CLI outside checkout"
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: receipt[key] for key in ("passed", "version")}))


if __name__ == "__main__":
    main()
