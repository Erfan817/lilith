#!/usr/bin/env python3
"""Bounded offline search of the actual v2 provenance manifests."""
import argparse
import json
from pathlib import Path
import sys

from validate import load_source_manifests


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Install root')
    parser.add_argument('--module', help='Exact module identifier, e.g. tarot or astrology')
    parser.add_argument('--query', default='', help='Case-insensitive substring in title, URL, topics or reading details')
    parser.add_argument('--limit', type=int, default=5, help='Returned records, 1..50 (default: 5)')
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 50:
        parser.error('--limit must be between 1 and 50')
    try:
        manifests = load_source_manifests(args.root)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    query = args.query.casefold()
    matches = []
    for path, data in manifests:
        if args.module is not None and data['module'] != args.module:
            continue
        for index, entry in enumerate(data['sources']):
            searchable = "\n".join((entry['url'], entry['title'], entry['role'], *entry['topics'],
                                     entry['retrieval']['status'], entry['retrieval']['method'],
                                     entry['retrieval']['detail'],
                                     entry.get('notes', '') if isinstance(entry.get('notes', ''), str)
                                     else "\n".join(entry['notes']))).casefold()
            if query not in searchable:
                continue
            compact = {key: entry[key] for key in ('url', 'title', 'accessed_at', 'accessed_precision',
                                                   'retrieval', 'topics', 'use_for_synthesis', 'role')}
            for key in ('accessed_on', 'accessed_reason'):
                if key in entry:
                    compact[key] = entry[key]
            compact.update(module=data['module'], manifest=path.relative_to(args.root).as_posix(), record_index=index)
            matches.append(compact)
    result = matches[:args.limit]
    print(json.dumps({'query': args.query, 'module': args.module, 'limit': args.limit,
                      'total_matches': len(matches), 'returned': len(result),
                      'has_more': len(matches) > len(result), 'sources': result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
