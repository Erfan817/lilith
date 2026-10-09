#!/usr/bin/env python3
"""Validate eval prompts/assertions; never substitute this for model execution."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description="离线评测数据检查，不执行模型或自动触发测试")
    parser.add_argument("--suite", type=Path, default=Path(__file__).resolve().parents[1] / "evals" / "evals.json")
    args = parser.parse_args()
    errors = []
    try:
        suite = json.loads(args.suite.read_text(encoding="utf-8"))
        if not isinstance(suite, dict):
            raise ValueError("评测文件必须是JSON对象")
        cases = suite.get("evals")
        if not isinstance(cases, list) or not cases:
            raise ValueError("evals 必须是非空列表")
        ids = set()
        for case in cases:
            if not isinstance(case, dict):
                errors.append("评测条目必须是对象")
                continue
            ident = case.get("id")
            if not isinstance(ident, str) or not ident or ident in ids:
                errors.append("案例id为空或重复")
            ids.add(str(ident))
            for field in ["prompt", "expected_output"]:
                if not isinstance(case.get(field), str) or not case[field].strip():
                    errors.append(f"{ident}: {field} 必须是非空字符串")
            if type(case.get("expected_trigger")) is not bool:
                errors.append(f"{ident}: expected_trigger 必须是布尔值")
            assertions = case.get("assertions")
            if not isinstance(assertions, list) or not assertions or any(not isinstance(a, str) or not a.strip() for a in assertions):
                errors.append(f"{ident}: 缺可验证断言")
            files = case.get("files")
            if not isinstance(files, list) or any(not isinstance(f, str) or not f for f in files):
                errors.append(f"{ident}: files 必须是字符串列表")
        positive = sum(c.get("expected_trigger") is True for c in cases if isinstance(c, dict))
        negative = sum(c.get("expected_trigger") is False for c in cases if isinstance(c, dict))
        if not positive or not negative:
            errors.append("必须同时有触发与不触发案例")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        cases, positive, negative = [], 0, 0
    payload = {"passed": not errors, "errors": errors, "case_count": len(cases),
               "positive_count": positive, "negative_count": negative,
               "model_evaluation_executed": False,
               "scope": "Only test-data integrity; real activation and interpretation require stored model responses and grading."}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
