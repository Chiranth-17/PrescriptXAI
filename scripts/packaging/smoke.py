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
    root = Path(tempfile.mkdtemp(prefix="prescriptxai-wheel-"))
    venv.create(root / "environment", with_pip=False)
    python = root / "environment" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "passed": False,
        "wheel": str(wheel),
        "environment": str(root),
        "dependencies": "Fresh runtime and API/dashboard dependencies constrained by uv.lock",
    }

    def run(stage, command):
        result = subprocess.run(
            command,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for suffix, contents in (
            ("stdout.log", result.stdout),
            ("stderr.log", result.stderr),
            ("exit", str(result.returncode) + "\n"),
        ):
            args.output.with_suffix(f".{stage}.{suffix}").write_text(contents, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(
                f"Wheel {stage} exited {result.returncode}. Inspect {args.output.parent}"
            )
        return result

    try:
        constraints = root / "constraints.txt"
        run(
            "export",
            [
                uv,
                "export",
                "--project",
                str(Path.cwd()),
                "--locked",
                "--all-groups",
                "--all-extras",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
                "--output-file",
                str(constraints),
            ],
        )
        run(
            "install",
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--constraint",
                str(constraints),
                str(wheel) + "[api,dashboard]",
            ],
        )
        result = run("import", [str(python), "-c", CHECK])
        run("cli", [str(python), "-m", "prescriptxai.cli", "--help"])
        receipt.update(json.loads(result.stdout))
        print(json.dumps({key: receipt[key] for key in ("passed", "version")}))
    finally:
        args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
