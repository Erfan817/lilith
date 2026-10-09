#!/usr/bin/env python3
"""One CLI for Lilith's supported computational paths."""
from pathlib import Path
import subprocess
import sys

ENGINES = {"tarot": "draw.py", "bazi": "bazi.py", "astrology": "astrology.py",
           "doctor": "doctor.py", "report": "report.py", "location": "location.py", "sources": "sources.py"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("占卜师莉莉丝 · Lilith Diviner\n用法: python scripts/lilith.py {" + ",".join(ENGINES) + "} [参数]\n紫微与奇门: 读取对应知识模块并提供可信外部盘面；此版无自动排盘。")
        return 0
    system, *args = argv
    if system in ("ziwei", "qimen"):
        print("此体系目前使用可信外部盘面：请提供盘面、来源与流派口径；不能伪造本地排盘结果。", file=sys.stderr)
        return 2
    if system not in ENGINES:
        print("未知命令，请选择 " + " / ".join(ENGINES) + "。", file=sys.stderr)
        return 2
    script = Path(__file__).resolve().parent / ENGINES[system]
    return subprocess.run([sys.executable, str(script), *args], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
