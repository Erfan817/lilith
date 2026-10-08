#!/usr/bin/env python3
"""Original RWS tarot draw: uniform sampling, never question/time weighted."""
import argparse
import json
import math
import random

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


def draw(spread, question="", seed=None, reversed_probability=0.5):
    if not math.isfinite(reversed_probability) or not 0 <= reversed_probability <= 1:
        raise ValueError("逆位概率必须是 0 到 1 的有限数值")
    rng = random.SystemRandom() if seed is None else random.Random(seed)
    names = rng.sample(DECK, len(SPREADS[spread]))
    return {
        "schema_version": "1.0",
        "spread": spread,
        "question": question,
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
    parser.add_argument("--question", default="")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--reversed-probability", type=float, default=0.5)
    args = parser.parse_args()
    try:
        result = draw(args.spread, args.question, args.seed, args.reversed_probability)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
