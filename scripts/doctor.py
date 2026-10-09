#!/usr/bin/env python3
"""Read-only dependency checks for the interpreter actually invoking Lilith."""
import argparse
import importlib.util
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import shlex
import sys

REQUIRED = {
    "tarot": {},
    "bazi": {"lunar_python": ("lunar-python", "1.4.8"), "tzdata": ("tzdata", "2025.2")},
    "astrology": {"astronomy": ("astronomy-engine", "2.1.19"), "tzdata": ("tzdata", "2025.2")},
}


def main():
    parser = argparse.ArgumentParser(description="只检查环境，不安装、不联网、不保存用户资料")
    parser.add_argument("--module", choices=["all", *REQUIRED], default="all")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    chosen = REQUIRED if args.module == "all" else {args.module: REQUIRED[args.module]}
    deps = {name: pair for requirements in chosen.values() for name, pair in requirements.items()}
    checks = []
    for import_name, (distribution, pinned) in deps.items():
        available = importlib.util.find_spec(import_name) is not None
        try:
            installed = version(distribution)
        except PackageNotFoundError:
            installed = None
        checks.append({"package": distribution, "required_version": pinned, "installed_version": installed,
                       "importable": available, "ready": available and installed == pinned})
    python_ready = sys.version_info >= (3, 10)
    commands = []
    if not all(check["ready"] for check in checks):
        commands.append([sys.executable, "-m", "pip", "install", "-r", str(root / "requirements.txt")])
    payload = {"schema_version": "1.0", "skill_name": "lilith-diviner", "module": args.module,
               "ready": python_ready and all(check["ready"] for check in checks),
               "python": {"executable": sys.executable, "version": sys.version.split()[0], "supported": python_ready},
               "dependencies": checks, "network_used": False, "installed_anything": False,
               "repair_argv": commands, "repair_shell_posix": [shlex.join(command) for command in commands],
               "guidance": "修复建议只展示，不执行；先确认使用本技能的独立虚拟环境。"}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
