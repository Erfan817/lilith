#!/usr/bin/env python3
"""Generate deterministic docs/stats.json from actual references and sources."""
import argparse
import json
from pathlib import Path
import sys

from validate import collect_stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Install root')
    parser.add_argument('--check', action='store_true', help='Fail if docs/stats.json is missing/stale; never write')
    args = parser.parse_args(argv)
    target = args.root / 'docs/stats.json'
    try:
        if not args.root.is_dir():
            raise ValueError(f'Install root is missing or not a directory: {args.root}')
        stats = collect_stats(args.root)
        rendered = json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
        if args.check:
            if not target.is_file():
                print(f'Missing stats file: {target}; run scripts/update_stats.py', file=sys.stderr)
                return 1
            if target.read_text(encoding='utf-8') != rendered:
                print(f'Stale stats file: {target}; run scripts/update_stats.py', file=sys.stderr)
                return 1
            print('docs/stats.json is current')
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding='utf-8')
        print('Updated docs/stats.json')
        return 0
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
