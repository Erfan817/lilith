#!/usr/bin/env python3
"""Original RWS tarot draw: uniform sampling, never question/time weighted."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

MAJORS = "愚者 魔术师 女祭司 女皇 皇帝 教皇 恋人 战车 力量 隐士 命运之轮 正义 倒吊人 死神 节制 恶魔 高塔 星星 月亮 太阳 审判 世界".split()
SUITS = ("权杖", "圣杯", "宝剑", "星币")
RANKS = "王牌 二 三 四 五 六 七 八 九 十 侍从 骑士 王后 国王".split()
DECK = MAJORS + [suit + rank for suit in SUITS for rank in RANKS]
SPREADS = {
    "single": ["当前指引"],
    "three": ["过去", "现在", "可能走向"],
    "diamond": ["核心", "根源", "阻力", "潜力", "建议"],
    "moon": ["新月", "上弦", "满月", "下弦"],
    "horseshoe": ["远期过去", "近期过去", "当前", "近期走向", "外部影响", "建议", "可能结果"],
    "celtic": ["核心", "交叉", "意识目标", "根基", "近期过去", "近期走向", "自我", "环境", "希望与恐惧", "可能结果"],
}


def draw(spread, question="", seed=None, reversed_probability=0.5, echo_question=False):
    if not math.isfinite(reversed_probability) or not 0 <= reversed_probability <= 1:
        raise ValueError("逆位概率必须是 0 到 1 的有限数值")
    rng = random.SystemRandom() if seed is None else random.Random(seed)
    names = rng.sample(DECK, len(SPREADS[spread]))
    return {
        "schema_version": "1.1",
        "spread": spread,
        "question": question if echo_question else None,
        "question_provided": bool(question),
        "question_echoed": echo_question,
        "deck": "Rider-Waite-Smith; Strength VIII; Justice XI",
        "algorithm": "uniform-without-replacement",
        "randomness": "system-random" if seed is None else "seeded-pseudorandom",
        "seed": seed,
        "reversed_probability": reversed_probability,
        "cards": [
            {"position": pos, "card": name, "orientation": "逆位" if rng.random() < reversed_probability else "正位", "is_major": name in MAJORS}
            for pos, name in zip(SPREADS[spread], names)
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="均匀、无放回塔罗抽牌；指定 seed 仅用于可复现实验")
    parser.add_argument("--spread", choices=SPREADS, default="three")
    questions = parser.add_mutually_exclusive_group()
    questions.add_argument("--question", default="", help="仅限已安全编码的程序参数；不推荐 shell 拼接")
    questions.add_argument("--question-file", help="从 UTF-8 文件读取问题；- 表示标准输入")
    parser.add_argument("--echo-question", action="store_true", help="显式允许问题原文进入 JSON 输出/宿主日志")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--reversed-probability", type=float, default=0.5)
    args = parser.parse_args()
    try:
        question = args.question
        if args.question_file:
            if args.question_file == "-":
                question = sys.stdin.read(65537)
            else:
                with Path(args.question_file).open("rb") as source:
                    raw = source.read(65537)
                if len(raw) > 65536:
                    raise ValueError("问题文件最多 65536 UTF-8 字节")
                question = raw.decode("utf-8")
        if len(question.encode("utf-8")) > 65536:
            raise ValueError("问题最多 65536 UTF-8 字节")
        result = draw(args.spread, question, args.seed, args.reversed_probability, args.echo_question)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
