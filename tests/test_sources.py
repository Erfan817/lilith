"""Source contracts and bounded real-manifest lookup; fixtures are synthetic."""
import copy
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    spec = importlib.util.spec_from_file_location('source_validate', ROOT / 'scripts/validate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(index=0):
    return {
        'url': f'https://example.com/source/{index}', 'title': f'Source {index}',
        'accessed_at': '2026-10-08T10:20:30Z', 'accessed_precision': 'instant',
        'retrieval': {'status': 'body_read', 'method': 'web_extract', 'detail': 'Main article read.'},
        'topics': ['topic'], 'use_for_synthesis': True, 'role': 'knowledge',
    }


def manifest(module='tarot', entries=None):
    return {'schema_version': 2, 'module': module, 'documents': ['cards.md'],
            'source_policy': 'Only actual readings support synthesis.',
            'sources': entries if entries is not None else [record()]}


def test_source_contract_accepts_complete_records():
    check = getattr(load_validator(), 'validate_source_manifest', None)
    assert callable(check), 'Missing source schema validator'
    assert check(manifest(), expected_module='tarot') == []


def write_manifest(root, data, filename='sources.json'):
    path = root / 'references' / data['module'] / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return path


@pytest.mark.parametrize('field, value', [
    ('schema_version', '2'), ('schema_version', True), ('module', 'Tarot'),
    ('module', 'bazi'), ('documents', 'cards.md'), ('documents', [False]),
    ('documents', ['../cards.md']), ('source_policy', ''), ('sources', {}),
    ('sources', []), ('source_count', 999),
])
def test_source_contract_rejects_invalid_envelope(field, value):
    data = manifest()
    data[field] = value
    errors = load_validator().validate_source_manifest(data, expected_module='tarot')
    assert any(field in error for error in errors)


@pytest.mark.parametrize('field', ['schema_version', 'module', 'documents', 'source_policy', 'sources'])
def test_source_contract_requires_envelope_fields(field):
    data = manifest()
    del data[field]
    assert any(field in error for error in load_validator().validate_source_manifest(data))


@pytest.mark.parametrize('field, value', [
    ('url', 'file:///secret'), ('url', 'https:///missing-host'), ('url', 'https://example.com/bad url'),
    ('url', 4), ('title', None), ('title', ' '), ('accessed_precision', 'minute'),
    ('topics', 'tarot'), ('topics', ['']), ('topics', [4]),
    ('use_for_synthesis', 1), ('role', ''), ('retrieval', 'body read'),
    ('notes', [1]), ('extensions', []),
])
def test_source_contract_rejects_invalid_record_fields(field, value):
    entry = record()
    entry[field] = value
    errors = load_validator().validate_source_manifest(manifest(entries=[entry]))
    assert any(f'sources[0].{field}' in error for error in errors)


@pytest.mark.parametrize('field', ['url', 'title', 'accessed_at', 'accessed_precision', 'retrieval', 'topics', 'use_for_synthesis', 'role'])
def test_source_contract_requires_each_record_field(field):
    entry = record()
    del entry[field]
    assert any(field in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


@pytest.mark.parametrize('field, value', [('status', ''), ('method', None), ('detail', []), ('status', 'invented')])
def test_source_contract_rejects_bad_retrieval_fields(field, value):
    entry = record()
    entry['retrieval'][field] = value
    errors = load_validator().validate_source_manifest(manifest(entries=[entry]))
    assert any(f'retrieval.{field}' in error for error in errors)


@pytest.mark.parametrize('field', ['status', 'method', 'detail'])
def test_source_contract_requires_retrieval_fields(field):
    entry = record()
    del entry['retrieval'][field]
    assert any(f'retrieval.{field}' in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


def test_source_contract_rejects_non_objects():
    check = load_validator().validate_source_manifest
    assert check([])
    assert check(manifest(entries=['wrong']))


def test_audit_checks_every_source_record_not_just_nonempty_json(tmp_path):
    root = tmp_path / 'example-skill'
    root.mkdir()
    (root / 'SKILL.md').write_text('---\nname: example-skill\ndescription: Use for documents\n---\n# Instructions\n')
    second = record(1)
    second['url'] = 'not a URL'
    write_manifest(root, manifest(entries=[record(), second]))
    errors, _ = load_validator().audit(root)
    assert any('sources[1].url' in error and 'sources.json' in error for error in errors)


@pytest.mark.parametrize('value', [None, '2026-10-08', '2026-02-30T12:00:00Z', '2026-10-08T12:00:00', '2026-10-08 12:00:00Z', 4])
def test_instant_access_time_requires_real_iso_instant_with_timezone(value):
    entry = record()
    entry['accessed_at'] = value
    assert any('accessed_at' in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


def test_date_only_history_keeps_date_and_does_not_invent_midnight():
    entry = record()
    entry.update(accessed_at=None, accessed_on='2026-10-08', accessed_precision='date',
                 accessed_reason='Legacy record retained only a calendar date, no time or timezone.')
    check = load_validator().validate_source_manifest
    assert check(manifest(entries=[entry])) == []
    entry['accessed_at'] = '2026-10-08T00:00:00Z'
    assert any('accessed_at' in error for error in check(manifest(entries=[entry])))


@pytest.mark.parametrize('value', [None, '2026-02-30', '2026-10-08T00:00:00Z'])
def test_date_precision_requires_valid_original_date(value):
    entry = record()
    entry.update(accessed_at=None, accessed_on=value, accessed_precision='date', accessed_reason='Date only.')
    assert any('accessed_on' in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


def test_unknown_access_time_requires_explicit_reason():
    entry = record()
    entry.update(accessed_at=None, accessed_precision='unknown')
    check = load_validator().validate_source_manifest
    assert any('accessed_reason' in error for error in check(manifest(entries=[entry])))
    entry['accessed_reason'] = 'No historical access date was recorded; migration does not backfill one.'
    assert check(manifest(entries=[entry])) == []


@pytest.mark.parametrize('status', ['metadata_only', 'index_only', 'image_only', 'blocked', 'failed', 'excluded', 'provenance_review'])
def test_non_content_records_cannot_be_marked_synthesis_evidence(status):
    entry = record()
    entry['retrieval']['status'] = status
    check = load_validator().validate_source_manifest
    assert any('use_for_synthesis' in error for error in check(manifest(entries=[entry])))
    entry['use_for_synthesis'] = False
    assert check(manifest(entries=[entry])) == []


def test_partial_read_is_distinct_and_duplicate_url_records_are_allowed():
    first = record()
    first['retrieval']['status'] = 'partial_body_read'
    second = record()
    second['retrieval']['status'] = 'blocked'
    second['use_for_synthesis'] = False
    assert load_validator().validate_source_manifest(manifest(entries=[first, second])) == []


@pytest.mark.parametrize('field, value', [('accessed_precision', []), ('retrieval', {'status': [], 'method': 'unknown', 'detail': 'Bad type'})])
def test_bad_json_field_types_return_errors_not_exceptions(field, value):
    entry = record()
    entry[field] = value
    assert load_validator().validate_source_manifest(manifest(entries=[entry]))


@pytest.mark.parametrize('url', ['https://example.com:bad/path', 'https://name:secret@example.com/path'])
def test_source_urls_reject_invalid_ports_or_embedded_credentials(url):
    entry = record()
    entry['url'] = url
    assert any('url' in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


def sources_cli(root, *args):
    return subprocess.run([sys.executable, str(ROOT / 'scripts/sources.py'), '--root', str(root), *args],
                          text=True, capture_output=True)


def test_sources_cli_default_is_bounded_and_reads_real_files(tmp_path):
    write_manifest(tmp_path, manifest(entries=[record(index) for index in range(9)]))
    result = sources_cli(tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['total_matches'] == 9
    assert data['returned'] == 5
    assert data['has_more'] is True
    assert len(data['sources']) == 5
    assert data['sources'][0]['url'] == 'https://example.com/source/0'
    assert data['sources'][0]['manifest'] == 'references/tarot/sources.json'
    assert data['sources'][0]['retrieval']['status'] == 'body_read'


def test_sources_main_serializes_windows_manifest_as_posix(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('source_lookup_test', ROOT / 'scripts/sources.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = PureWindowsPath('C:/synthetic-skill')
    path = root / 'references' / 'tarot' / 'sources.json'
    assert str(path.relative_to(root)) == r'references\tarot\sources.json'
    def load_windows_manifests(received_root):
        assert type(received_root) is PureWindowsPath
        assert received_root == root
        return [(path, manifest())]

    def windows_path_factory(value):
        if value == root.as_posix():
            return root
        return Path(value)

    monkeypatch.setattr(module, 'Path', windows_path_factory)
    monkeypatch.setattr(module, 'load_source_manifests', load_windows_manifests)

    assert module.main(['--root', root.as_posix()]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data['returned'] == data['total_matches'] == 1
    assert data['sources'][0]['manifest'] == 'references/tarot/sources.json'


def test_sources_cli_filters_module_and_casefolded_query_before_limit(tmp_path):
    write_manifest(tmp_path, manifest(entries=[record(i) for i in range(7)]))
    write_manifest(tmp_path, manifest(module='bazi', entries=[record(20)]))
    result = sources_cli(tmp_path, '--module', 'tarot', '--query', 'SOURCE 6', '--limit', '1')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['total_matches'] == 1
    assert data['sources'][0]['title'] == 'Source 6'
    assert data['sources'][0]['module'] == 'tarot'
    assert data['returned'] == 1 and data['has_more'] is False


def test_sources_cli_matches_chinese_topics_and_preserves_failed_records(tmp_path):
    entry = record()
    entry.update(topics=['四化'], use_for_synthesis=False)
    entry['retrieval']['status'] = 'failed'
    entry['extensions'] = {'long_history': 'x' * 10000}
    write_manifest(tmp_path, manifest(module='ziwei', entries=[entry]))
    result = sources_cli(tmp_path, '--query', '四化')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['sources'][0]['retrieval']['status'] == 'failed'
    assert data['sources'][0]['use_for_synthesis'] is False
    assert 'extensions' not in data['sources'][0]


@pytest.mark.parametrize('limit', ['0', '-1', '51', 'NaN'])
def test_sources_cli_rejects_out_of_bounds_limit(tmp_path, limit):
    write_manifest(tmp_path, manifest())
    result = sources_cli(tmp_path, '--limit', limit)
    assert result.returncode == 2
    assert 'limit' in result.stderr and 'Traceback' not in result.stderr


def test_sources_cli_no_match_has_accurate_empty_totals(tmp_path):
    write_manifest(tmp_path, manifest())
    result = sources_cli(tmp_path, '--query', 'not-present')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['sources'] == []
    assert data['total_matches'] == data['returned'] == 0
    assert data['has_more'] is False


def test_sources_cli_reports_invalid_manifest_instead_of_partial_success(tmp_path):
    write_manifest(tmp_path, manifest(), 'sources-good.json')
    bad = record()
    bad['title'] = None
    write_manifest(tmp_path, manifest(entries=[bad]), 'sources-bad.json')
    result = sources_cli(tmp_path)
    assert result.returncode == 1
    assert 'sources-bad.json' in result.stderr and 'title' in result.stderr
    assert 'Traceback' not in result.stderr and not result.stdout.strip()


def test_all_six_repository_manifests_use_v2_and_retain_every_historical_record():
    expected_legacy_counts = {
        'astrology/sources-advanced.json': 46, 'astrology/sources-basic.json': 79,
        'bazi/sources.json': 4, 'qimen/sources.json': 8,
        'tarot/sources.json': 9, 'ziwei/sources.json': 14,
    }
    paths = sorted((ROOT / 'references').glob('*/sources*.json'))
    assert len(paths) == len(expected_legacy_counts)
    check = load_validator().validate_source_manifest
    for path in paths:
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data.get('schema_version') == 2, str(path)
        assert check(data, expected_module=path.parent.name) == [], str(path)
        name = path.relative_to(ROOT / 'references').as_posix()
        historical = [s for s in data['sources'] if 'legacy' in s.get('extensions', {})]
        assert len(historical) == expected_legacy_counts[name]
        for entry in historical:
            legacy = entry['extensions']['legacy']
            if legacy.get('accessed_at'):
                assert entry['accessed_at'] == legacy['accessed_at']
            elif legacy.get('accessed_on'):
                assert entry['accessed_at'] is None
                assert entry['accessed_on'] == legacy['accessed_on']
                assert entry['accessed_precision'] == 'date'
            else:
                assert entry['accessed_at'] is None and entry['accessed_precision'] == 'unknown'
            if legacy.get('used_for_synthesis') is False:
                assert entry['use_for_synthesis'] is False


def test_dependency_metadata_supplement_is_not_a_historical_read_timestamp():
    data = json.loads((ROOT / 'references/bazi/sources.json').read_text())
    entries = [entry for entry in data['sources'] if entry['url'].startswith('https://github.com/')]
    assert len(entries) == 2
    for entry in entries:
        assert entry.get('accessed_at') is None
        assert entry.get('accessed_precision') == 'unknown'
        metadata = entry.get('extensions', {}).get('metadata_retrieval', {})
        assert metadata.get('status') == 'metadata_only'
        assert metadata.get('accessed_at')
        assert metadata.get('method') == 'GitHub API'


def test_stats_deduplicate_urls_but_count_distinct_read_attempts(tmp_path):
    first = record(1)
    failed = record(1)
    failed['retrieval']['status'] = 'blocked'
    failed['use_for_synthesis'] = False
    write_manifest(tmp_path, manifest(entries=[first, failed]))
    write_manifest(tmp_path, manifest(module='bazi', entries=[record(1), record(2)]))
    stats = load_validator().collect_stats(tmp_path)
    assert stats['source_manifests'] == 2
    assert stats['source_records'] == 4
    assert stats['source_unique_urls'] == 2
    assert stats['synthesis_source_records'] == 3
    assert stats['synthesis_source_unique_urls'] == 2
    assert stats['source_statuses'] == {'blocked': 1, 'body_read': 3}
    assert stats['accessed_precisions'] == {'instant': 4}
    assert stats['modules']['tarot']['source_records'] == 2
    assert stats['modules']['tarot']['source_unique_urls'] == 1
    manifests = {item['file']: item for item in stats['source_manifest_stats']}
    assert manifests['references/tarot/sources.json']['records'] == 2
    assert manifests['references/tarot/sources.json']['unique_urls'] == 1


def test_source_stats_do_not_report_success_for_invalid_sources(tmp_path):
    bad = record()
    bad['accessed_at'] = 'invalid-time'
    write_manifest(tmp_path, manifest(entries=[bad]))
    with pytest.raises(ValueError, match='accessed_at'):
        load_validator().collect_stats(tmp_path)


def test_published_json_schema_defines_core_and_history_fields():
    path = ROOT / 'docs/source-schema.json'
    assert path.is_file(), 'Missing published source JSON Schema'
    schema = json.loads(path.read_text())
    assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
    assert set(schema['required']) == {'schema_version', 'module', 'documents', 'source_policy', 'sources'}
    assert schema['properties']['schema_version']['const'] == 2
    source = schema['$defs']['source']
    assert set(source['required']) == {'url', 'title', 'accessed_at', 'accessed_precision', 'retrieval', 'topics', 'use_for_synthesis', 'role'}
    assert source['properties']['accessed_precision']['enum'] == ['instant', 'date', 'unknown']
    assert source['properties']['use_for_synthesis']['type'] == 'boolean'
    assert 'accessed_reason' in source['properties'] and 'accessed_on' in source['properties']


@pytest.mark.parametrize('value', ['2026-10-08T12:00:00+00:60', '2026-10-08T12:00:00+24:00'])
def test_instant_rejects_out_of_range_timezone_components(value):
    entry = record()
    entry['accessed_at'] = value
    assert any('accessed_at' in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


def test_unknown_precision_cannot_hide_an_original_access_date():
    entry = record()
    entry.update(accessed_at=None, accessed_precision='unknown', accessed_on='2026-10-08', accessed_reason='Historical date exists.')
    assert any('accessed_precision' in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


@pytest.mark.parametrize('field, value', [('accessed_on', 'invalid-date'), ('accessed_reason', 4)])
def test_optional_history_fields_are_validated_even_with_instant_precision(field, value):
    entry = record()
    entry[field] = value
    assert any(field in error for error in load_validator().validate_source_manifest(manifest(entries=[entry])))


def test_compact_cli_does_not_match_field_names_as_source_text(tmp_path):
    write_manifest(tmp_path, manifest())
    result = sources_cli(tmp_path, '--query', 'retrieval')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['total_matches'] == 0


def test_sources_cli_missing_install_root_is_an_error(tmp_path):
    result = sources_cli(tmp_path / 'missing-root')
    assert result.returncode == 1
    assert 'root' in result.stderr and 'Traceback' not in result.stderr


def test_sources_cli_invalid_json_is_reported_with_manifest_path(tmp_path):
    path = write_manifest(tmp_path, manifest())
    path.write_text('not valid JSON')
    result = sources_cli(tmp_path)
    assert result.returncode == 1
    assert 'sources.json' in result.stderr and 'Traceback' not in result.stderr


def test_source_manifest_loader_ignores_runtime_candidates(tmp_path):
    write_manifest(tmp_path, manifest())
    invalid_runtime = tmp_path / 'references/.pytest_cache/sources-runtime.json'
    invalid_runtime.parent.mkdir()
    invalid_runtime.write_text('Not project data')
    result = sources_cli(tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['total_matches'] == 1


@pytest.mark.parametrize('field', ['title', 'role', 'topics', 'retrieval'])
def test_source_unicode_surrogates_are_rejected_before_cli_output(tmp_path, field):
    entry = record()
    if field == 'topics':
        entry[field] = [chr(0xD800)]
    elif field == 'retrieval':
        entry[field]['detail'] = chr(0xD800)
    else:
        entry[field] = chr(0xD800)
    errors = load_validator().validate_source_manifest(manifest(entries=[entry]))
    assert errors, 'Unsafe Unicode passed source validation'
    path = tmp_path / 'references' / 'tarot' / 'sources.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest(entries=[entry]), ensure_ascii=True), encoding='utf-8')
    result = sources_cli(tmp_path)
    assert result.returncode == 1
    assert 'Traceback' not in result.stderr
    assert not result.stdout.strip()
