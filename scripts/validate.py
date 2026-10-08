#!/usr/bin/env python3
"""Offline audit of this single skill's structure, links and declared coverage."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import sys

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


def audit(root):
    import yaml
    root = Path(root).resolve()
    errors = []
    skills = [p for p in root.rglob("SKILL.md") if not any(part in {".git", ".venv"} for part in p.parts)]
    if len(skills) != 1 or not (root / "SKILL.md").is_file():
        errors.append(f"Expected 1 root SKILL.md, got {len(skills)}")
    skill = root / "SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n(.+)\Z", text, re.S)
        if not match:
            errors.append("SKILL.md lacks valid YAML delimiters or body")
        else:
            try:
                front = yaml.safe_load(match.group(1))
                for field in ("name", "description", "version", "author", "license", "platforms"):
                    if not isinstance(front, dict) or not front.get(field):
                        errors.append(f"SKILL.md missing {field}")
                description = front.get("description", "") if isinstance(front, dict) else ""
                if not isinstance(description, str) or len(description) > 60 or not description.endswith("."):
                    errors.append("Description must be a sentence no longer than 60 characters")
            except yaml.YAMLError as exc:
                errors.append(f"Invalid frontmatter: {exc}")
    all_md = [p for p in root.rglob("*.md") if not any(part in {".git", ".venv"} for part in p.parts)]
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
    for module, names in MODULE_FILES.items():
        for name in names:
            path = root / "references" / module / f"{name}.md"
            if not path.is_file() or len(path.read_text(encoding="utf-8")) < 300:
                errors.append(f"Missing/substantially empty reference: references/{module}/{name}.md")
    cards_path = root / "references/tarot/cards.md"
    draw_path = root / "scripts/draw.py"
    if cards_path.is_file() and draw_path.is_file():
        spec = importlib.util.spec_from_file_location("mystic_draw_audit", draw_path)
        draw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(draw)
        text = cards_path.read_text(encoding="utf-8")
        for name in draw.DECK:
            if name not in text:
                errors.append(f"Tarot reference missing card: {name}")
        if len(draw.DECK) != 78 or len(set(draw.DECK)) != 78:
            errors.append("Deck must have exactly 78 distinct cards")
    signs_path = root / "references/astrology/zodiac-signs.md"
    if signs_path.is_file():
        text = signs_path.read_text(encoding="utf-8")
        for sign in "白羊 金牛 双子 巨蟹 狮子 处女 天秤 天蝎 射手 摩羯 水瓶 双鱼".split():
            if sign not in text:
                errors.append(f"Zodiac reference missing sign: {sign}")
    source_files = list((root / "references").rglob("sources*.json")) if (root / "references").exists() else []
    for path in source_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, (dict, list)) or not data:
                errors.append(f"Empty source manifest: {path.relative_to(root)}")
        except (ValueError, OSError) as exc:
            errors.append(f"Invalid source manifest {path.relative_to(root)}: {exc}")
    for path in (root / "scripts").rglob("*.py") if (root / "scripts").exists() else []:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Invalid Python {path.relative_to(root)}: {exc}")
    stats = {
        "skill_entries": len(skills), "reference_files": sum(len(names) for names in MODULE_FILES.values()),
        "astrology_topics": len(ASTROLOGY_FILES), "markdown_files": len(all_md),
        "source_manifests": len(source_files), "reference_characters": sum(len(p.read_text(encoding="utf-8")) for p in all_md if "references" in p.parts),
    }
    return errors, stats


def main():
    errors, stats = audit(Path(__file__).resolve().parents[1])
    print(json.dumps({"passed": not errors, "errors": errors, "stats": stats}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
