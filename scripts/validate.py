#!/usr/bin/env python3
"""Offline audit of this single skill's structure, links and declared coverage."""
import ast
import argparse
from collections import Counter
from datetime import date, datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ASTROLOGY_FILES = (
    "foundations", "zodiac-signs", "planets", "houses", "aspects", "dignities", "moon-nodes", "chart-reading",
    "synastry", "timing", "traditional-techniques", "schools-and-history", "astronomy-and-calculation", "glossary", "coverage",
)
MODULE_FILES = {
    "tarot": ("cards", "spreads", "relations", "reading"),
    "bazi": ("workflow", "wuxing-tables", "shichen-table", "dayun-rules", "shensha-table", "classical-texts"),
    "qimen": ("workflow", "rules-and-schools", "interpretation"),
    "ziwei": ("workflow", "palaces-and-stars", "sihua-and-timing"),
    "astrology": ASTROLOGY_FILES,
    "common": ("reading-protocol", "data-contracts"),
}
IGNORED_DIRECTORIES = {".git", ".venv", ".pytest_cache", "__pycache__"}


def validate_frontmatter(front, root):
    """Agent Skills fields; no Hermes-specific authoring limits."""
    if not isinstance(front, dict):
        return ["SKILL.md frontmatter must be a mapping"]
    errors = []
    allowed = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
    for field in front:
        if field not in allowed:
            errors.append(f"Unexpected frontmatter field: {field}; put extra properties in metadata")
    name = front.get("name")
    if (not isinstance(name, str) or not 1 <= len(name) <= 64 or name != name.lower()
            or name.startswith("-") or name.endswith("-") or "--" in name
            or not all(c.isalnum() or c == "-" for c in name)):
        errors.append("SKILL.md name must be 1..64 lowercase alphanumeric/hyphen characters without edge or repeated hyphens")
    elif name != Path(root).name:
        errors.append(f"SKILL.md name {name!r} must match install root directory {Path(root).name!r}")
    description = front.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        errors.append("SKILL.md description must be a non-empty string of 1..1024 characters")
    if "compatibility" in front:
        value = front["compatibility"]
        if not isinstance(value, str) or not value.strip() or len(value) > 500:
            errors.append("SKILL.md compatibility must be a non-empty string of 1..500 characters")
    for field in ("license", "allowed-tools"):
        if field in front and not isinstance(front[field], str):
            errors.append(f"SKILL.md {field} must be a string")
    if "metadata" in front:
        value = front["metadata"]
        if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            errors.append("SKILL.md metadata must be a mapping from strings to strings")
    return errors


def validate_project_metadata(front):
    """Lilith's Chinese activation/boundary policy, not the general spec."""
    description = front.get("description", "") if isinstance(front, dict) else ""
    description = description if isinstance(description, str) else ""
    errors = []
    if not re.search(r"[\u3400-\u9fff]", description):
        errors.append("Project description 必须包含中文")
    topics = ("塔罗", "八字", "紫微", "奇门", "星座", "占星")
    if not any(topic in description for topic in topics) or not re.search(r"用户|询问|当|时使用|用于.*问题|适用", description):
        errors.append("Project description 必须说明中文领域触发条件，而非只有关键词")
    if "不用于" not in description:
        errors.append("Project description 必须包含不用于边界")
    return errors


def validate_source_manifest(data, *, expected_module=None):
    """Validate the v2 source contract, returning all discovered errors."""
    if not isinstance(data, dict):
        return ["Source manifest must be an object"]
    try:
        json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (UnicodeError, ValueError, TypeError, RecursionError):
        return ["Source manifest contains invalid Unicode or non-JSON values; no unsafe text is echoed"]
    errors = []
    required = {"schema_version", "module", "documents", "source_policy", "sources"}
    for field in sorted(required - data.keys()):
        errors.append(f"{field}: required")
    for field in data.keys() - (required | {"extensions"}):
        errors.append(f"{field}: unsupported envelope field; retain legacy details in extensions")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 2:
        errors.append("schema_version: must be integer 2")
    module = data.get("module")
    if not isinstance(module, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", module):
        errors.append("module: must be a lowercase module identifier")
    elif expected_module is not None and module != expected_module:
        errors.append(f"module: {module!r} must match directory {expected_module!r}")
    documents = data.get("documents")
    if not isinstance(documents, list) or not documents or any(
            not isinstance(v, str) or not v.endswith(".md") or "\\" in v
            or Path(v).is_absolute() or ".." in Path(v).parts for v in documents):
        errors.append("documents: must be a non-empty list of module-relative Markdown paths")
    policy = data.get("source_policy")
    if not isinstance(policy, str) or not policy.strip():
        errors.append("source_policy: must be a non-empty string")
    if "extensions" in data and not isinstance(data["extensions"], dict):
        errors.append("extensions: must be an object")
    entries = data.get("sources")
    if not isinstance(entries, list) or not entries:
        errors.append("sources: must be a non-empty list")
        return errors
    fields = {"url", "title", "accessed_at", "accessed_precision", "retrieval", "topics", "use_for_synthesis", "role"}
    statuses = {"body_read", "sections_read", "partial_body_read", "code_read", "provenance_review",
                "metadata_only", "index_only", "image_only", "blocked", "failed", "excluded"}
    for index, entry in enumerate(entries):
        prefix = f"sources[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        for field in sorted(fields - entry.keys()):
            errors.append(f"{prefix}.{field}: required")
        url = entry.get("url")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
            valid_url = (parsed is not None and parsed.scheme in {"http", "https"} and parsed.hostname
                         and parsed.username is None and parsed.password is None
                         and (parsed.port is None or 1 <= parsed.port <= 65535)
                         and not any(c.isspace() or ord(c) < 32 for c in url))
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append(f"{prefix}.url: must be an absolute HTTP(S) URL without whitespace")
        for field in ("title", "role"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"{prefix}.{field}: must be a non-empty string")
        precision = entry.get("accessed_precision")
        accessed = entry.get("accessed_at")
        if precision not in ("instant", "date", "unknown"):
            errors.append(f"{prefix}.accessed_precision: must be instant, date or unknown")
        elif precision == "instant":
            try:
                if not isinstance(accessed, str) or not re.fullmatch(
                        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)", accessed):
                    raise ValueError("Not an offset-aware ISO instant")
                datetime.fromisoformat(accessed.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{prefix}.accessed_at: instant precision requires a valid ISO datetime with timezone")
        else:
            if accessed is not None:
                errors.append(f"{prefix}.accessed_at: must be null for date/unknown historical precision")
            reason = entry.get("accessed_reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{prefix}.accessed_reason: required when no historical instant is known")
        if precision == "date" or "accessed_on" in entry:
            original_date = entry.get("accessed_on")
            try:
                if not isinstance(original_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", original_date):
                    raise ValueError("Not an ISO date")
                date.fromisoformat(original_date)
            except ValueError:
                errors.append(f"{prefix}.accessed_on: requires a valid original ISO date")
            if precision == "unknown":
                errors.append(f"{prefix}.accessed_precision: an original accessed_on date requires date precision")
        if "accessed_reason" in entry and (not isinstance(entry["accessed_reason"], str) or not entry["accessed_reason"].strip()):
            errors.append(f"{prefix}.accessed_reason: must be a non-empty string")
        topics = entry.get("topics")
        if not isinstance(topics, list) or any(not isinstance(v, str) or not v.strip() for v in topics):
            errors.append(f"{prefix}.topics: must be a list of non-empty strings")
        if type(entry.get("use_for_synthesis")) is not bool:
            errors.append(f"{prefix}.use_for_synthesis: must be a boolean")
        retrieval = entry.get("retrieval")
        if not isinstance(retrieval, dict):
            errors.append(f"{prefix}.retrieval: must be an object")
        else:
            for field in ("status", "method", "detail"):
                if not isinstance(retrieval.get(field), str) or not retrieval[field].strip():
                    errors.append(f"{prefix}.retrieval.{field}: must be a non-empty string")
            if not isinstance(retrieval.get("status"), str) or retrieval["status"] not in statuses:
                errors.append(f"{prefix}.retrieval.status: unsupported reading status")
            if entry.get("use_for_synthesis") is True and retrieval.get("status") not in (
                    "body_read", "sections_read", "partial_body_read", "code_read"):
                errors.append(f"{prefix}.use_for_synthesis: only actually read content can support synthesis")
        notes = entry.get("notes")
        if "notes" in entry and not (isinstance(notes, str) or isinstance(notes, list)
                                      and all(isinstance(v, str) for v in notes)):
            errors.append(f"{prefix}.notes: must be a string or list of strings")
        if "extensions" in entry and not isinstance(entry["extensions"], dict):
            errors.append(f"{prefix}.extensions: must be an object")
    return errors


def load_source_manifests(root):
    """Read and validate every discovered manifest before returning any."""
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"Install root is missing or not a directory: {root}")
    loaded = []
    errors = []
    for path in sorted((root / "references").rglob("sources*.json")):
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            problems = validate_source_manifest(data, expected_module=path.parent.name)
            errors.extend(f"{path.relative_to(root)}: {error}" for error in problems)
            if not problems:
                loaded.append((path, data))
        except (ValueError, OSError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
    if errors:
        raise ValueError("\n".join(errors))
    return loaded


def collect_stats(root):
    """Deterministic inventory of files actually present, not declared totals."""
    root = Path(root)
    all_md = sorted(p for p in root.rglob("*.md") if not any(part in IGNORED_DIRECTORIES for part in p.relative_to(root).parts))
    references = [p for p in all_md if p.relative_to(root).parts[0] == "references"]
    modules = {}
    reference_characters = 0
    for path in references:
        relative = path.relative_to(root / "references")
        module = relative.parts[0] if len(relative.parts) > 1 else "_root"
        text = path.read_text(encoding="utf-8")
        info = modules.setdefault(module, {"reference_files": 0, "reference_characters": 0, "han_characters": 0})
        info["reference_files"] += 1
        info["reference_characters"] += len(text)
        info["han_characters"] += len(re.findall(r"[\u3400-\u9fff]", text))
        reference_characters += len(text)
    manifests = load_source_manifests(root)
    records = []
    manifest_stats = []
    by_module = {}
    for path, data in manifests:
        entries = data["sources"]
        records.extend(entries)
        by_module.setdefault(data["module"], []).extend(entries)
        manifest_stats.append({"file": path.relative_to(root).as_posix(), "module": data["module"],
                               "records": len(entries), "unique_urls": len({s["url"] for s in entries}),
                               "synthesis_records": sum(s["use_for_synthesis"] for s in entries),
                               "retrieval_statuses": dict(sorted(Counter(s["retrieval"]["status"] for s in entries).items()))})
    for module, entries in by_module.items():
        info = modules.setdefault(module, {"reference_files": 0, "reference_characters": 0, "han_characters": 0})
        info.update(source_records=len(entries), source_unique_urls=len({s["url"] for s in entries}),
                    synthesis_source_records=sum(s["use_for_synthesis"] for s in entries))
    return {
        "schema_version": 1, "skill_entries": sum(p.name == "SKILL.md" for p in all_md),
        "reference_files": len(references), "required_core_reference_files": sum(map(len, MODULE_FILES.values())),
        "astrology_topics": modules.get("astrology", {}).get("reference_files", 0),
        "required_core_astrology_topics": len(ASTROLOGY_FILES), "markdown_files": len(all_md),
        "source_manifests": len(manifests), "source_manifest_stats": manifest_stats,
        "source_records": len(records), "source_unique_urls": len({s["url"] for s in records}),
        "synthesis_source_records": sum(s["use_for_synthesis"] for s in records),
        "synthesis_source_unique_urls": len({s["url"] for s in records if s["use_for_synthesis"]}),
        "source_statuses": dict(sorted(Counter(s["retrieval"]["status"] for s in records).items())),
        "accessed_precisions": dict(sorted(Counter(s["accessed_precision"] for s in records).items())),
        "reference_characters": reference_characters, "modules": dict(sorted(modules.items())),
    }


def audit(root, *, project=False):
    import yaml
    root = Path(root).resolve()
    errors = []
    skills = [p for p in root.rglob("SKILL.md") if not any(part in IGNORED_DIRECTORIES for part in p.relative_to(root).parts)]
    if not (root / "SKILL.md").is_file() or (project and len(skills) != 1):
        errors.append(f"Expected 1 root SKILL.md, got {len(skills)}")
    skill = root / "SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n(.+)\Z", text, re.S)
        if not match or not match.group(2).strip():
            errors.append("SKILL.md lacks valid YAML delimiters or body")
        else:
            try:
                front = yaml.safe_load(match.group(1))
                errors.extend(validate_frontmatter(front, root))
                if project:
                    errors.extend(validate_project_metadata(front))
            except yaml.YAMLError as exc:
                errors.append(f"Invalid frontmatter: {exc}")
    all_md = [p for p in root.rglob("*.md") if not any(part in IGNORED_DIRECTORIES for part in p.relative_to(root).parts)]
    for path in all_md:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            target_path = target.split("#", 1)[0]
            if target_path and not (path.parent / target_path).exists():
                errors.append(f"{path.relative_to(root)}: missing reference {target_path}")
        if path == skill and re.search(r"/(?:home|Users)/[A-Za-z0-9_-]+/", text):
            errors.append("SKILL.md contains a machine-local absolute path")
    for module, names in (MODULE_FILES.items() if project else ()):
        for name in names:
            path = root / "references" / module / f"{name}.md"
            if not path.is_file() or len(path.read_text(encoding="utf-8")) < 300:
                errors.append(f"Missing/substantially empty reference: references/{module}/{name}.md")
    cards_path = root / "references/tarot/cards.md"
    if project and cards_path.is_file():
        # Trusted audit vocabulary, not an import from the directory being inspected.
        majors = "愚者 魔术师 女祭司 女皇 皇帝 教皇 恋人 战车 力量 隐士 命运之轮 正义 倒吊人 死神 节制 恶魔 高塔 星星 月亮 太阳 审判 世界".split()
        deck = majors + [suit + rank for suit in ("权杖", "圣杯", "宝剑", "星币")
                         for rank in "王牌 二 三 四 五 六 七 八 九 十 侍从 骑士 王后 国王".split()]
        text = cards_path.read_text(encoding="utf-8")
        for name in deck:
            if name not in text:
                errors.append(f"Tarot reference missing card: {name}")
    signs_path = root / "references/astrology/zodiac-signs.md"
    if project and signs_path.is_file():
        text = signs_path.read_text(encoding="utf-8")
        for sign in "白羊 金牛 双子 巨蟹 狮子 处女 天秤 天蝎 射手 摩羯 水瓶 双鱼".split():
            if sign not in text:
                errors.append(f"Zodiac reference missing sign: {sign}")
    source_files = [p for p in (root / "references").rglob("sources*.json")
                    if not any(part in IGNORED_DIRECTORIES for part in p.relative_to(root).parts)]
    for path in source_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(f"{path.relative_to(root)}: {error}" for error in
                          validate_source_manifest(data, expected_module=path.parent.name))
        except (ValueError, OSError) as exc:
            errors.append(f"Invalid source manifest {path.relative_to(root)}: {exc}")
    for path in (root / "scripts").rglob("*.py") if (root / "scripts").exists() else []:
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Invalid Python {path.relative_to(root)}: {exc}")
    try:
        stats = collect_stats(root)
    except ValueError as exc:
        if not any("sources" in error for error in errors):
            errors.extend(str(exc).splitlines())
        stats = {"unavailable": "Source validation failed; no partially successful counts are published"}
    return errors, stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Install root whose directory must match name")
    parser.add_argument("--generic", action="store_true", help="Agent Skills and source contracts only; omit Lilith content/Chinese trigger checks")
    args = parser.parse_args(argv)
    errors, stats = audit(args.root, project=not args.generic)
    print(json.dumps({"passed": not errors, "errors": errors, "stats": stats}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
