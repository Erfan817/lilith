"""Traceability of the published library; no network or book bodies."""
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def library():
    return json.loads((ROOT / "docs/library-index.json").read_text(encoding="utf-8"))


def test_every_library_entry_is_locatable_and_uses_registered_sources():
    data = library()
    entries = data["entries"]
    assert entries and len({item["id"] for item in entries}) == len(entries)
    registered = set()
    for manifest in (ROOT / "references").rglob("sources*.json"):
        records = json.loads(manifest.read_text(encoding="utf-8"))
        registered.update(record["url"] for record in records["sources"])
    for item in entries:
        path = item.get("reference_path", "")
        assert path, f"{item['id']}: missing reference_path"
        assert chr(92) not in path
        relative = PurePosixPath(path)
        assert not relative.is_absolute() and ".." not in relative.parts
        target = ROOT.joinpath(*relative.parts)
        assert target.is_file(), (item["id"], path)
        assert item.get("locator"), f"{item['id']}: missing locator"
        assert item.get("source_urls"), f"{item['id']}: missing source_urls"
        assert set(item["source_urls"]) <= registered, item["id"]
        assert item.get("reading_status") in {
            "sections_read", "partial_body_read", "metadata_only",
            "sections_read_prior", "secondary_body_read",
        }, item["id"]


def test_library_counts_match_actual_entries():
    data = library()
    actual = {
        "entries": len(data["entries"]),
        "books": sum(item["kind"] == "book" for item in data["entries"]),
        "cases": sum(item["kind"] == "case" for item in data["entries"]),
    }
    assert data.get("counts") == actual


def test_skill_entry_links_to_on_demand_library_and_evidence_rules():
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for relative in (
        "references/common/research-reading-guide.md",
        "references/common/experiments-and-evidence.md",
        "references/tarot/books-and-cases.md",
        "references/bazi/books-and-cases.md",
        "references/astrology/books-and-cases.md",
    ):
        assert relative in content, relative


def test_catalog_sources_cannot_be_used_as_translation_body_evidence():
    manifest = json.loads((ROOT / "references/astrology/sources-advanced.json").read_text(encoding="utf-8"))
    record = next(item for item in manifest["sources"]
                  if item["url"] == "http://projecthindsight.com/archives/hellenistic.html")
    assert record["retrieval"]["status"] == "metadata_only"
    assert record["role"] == "bibliography"
    assert record["use_for_synthesis"] is False
    entry = next(item for item in library()["entries"] if item["id"] == "case-hellenistic-revival")
    assert entry["evidence_level"].startswith("metadata_only")


def test_later_reading_event_keeps_the_original_partial_read():
    manifest = json.loads((ROOT / "references/bazi/sources.json").read_text(encoding="utf-8"))
    record = next(item for item in manifest["sources"] if item["title"].startswith("滴天髓闡微"))
    events = record.get("extensions", {}).get("reading_events", [])
    assert any(event["retrieval"]["status"] == "partial_body_read" for event in events)
    assert any("官杀" in " ".join(event["sections_read"]) for event in events)
    assert "官杀" in record["retrieval"]["detail"]

