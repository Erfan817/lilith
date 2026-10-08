# 数据与能力契约

## 随机抽牌

入口：`scripts/draw.py`。JSON 包含 `schema_version`、`spread`、`question`、`deck`、`algorithm`、`randomness`、`seed`、`reversed_probability`、`cards`。每张牌有 `position/card/orientation/is_major`。

默认 `SystemRandom` 均匀无放回抽取78牌，无问题和时间权重。`--seed` 明确标记 `seeded-pseudorandom`，是复现实验不是密码学随机，也没有超自然保证。指定逆位概率属于玩法口径，不是现实事件概率。

## 八字

入口：`scripts/bazi.py`。出生公历或农历、闰月、钟点/时辰、传统男女顺逆参数。默认 JSON，固定 UTC+08:00 和 23:00 换日。列年/月/日/时的 `gan/zhi/ten_god/hidden_stems`、`dayun`、`current_year`、`warnings`。

`--place` 只做展示与提示。公农换算和闰月用 `lunar-python==1.4.8`，旧内核的置闰转换不用于统一入口。干支、节气与大运内核放在 `scripts/vendor/bazi/`，由包装传入确认后的公历与农历展示；节气为简式近似，不知道时辰或节气临界以 `warnings` 为准。不要把内核文档当未检验的精度保证。分析/逝世年份限制在1900–2100，死亡不得早于出生或超过分析截止，不允许无界流年列表。

## 占星

入口：`scripts/astrology.py`。范围统一按 UTC 瞬间 `[1900-01-01T00:00Z, 2101-01-01T00:00Z)` 判断，显式偏移与 IANA 输入同一时刻必须等价；明确 UTC 偏移，或日期时间配 IANA 时区。指定经纬度后计算 ASC/DSC/MC/IC、整宫/等宫。默认热带黄道，地心视位置和真春分点日期坐标，不是 Swiss Ephemeris。

十天体为 Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn/Uranus/Neptune/Pluto；位置由 Astronomy Engine 计算。相位为合、六合、刑、拱、冲的黄经差，不计算赤纬平行，不默认相位状态入相/出相。速度用前后0.05日有限差分，留前后接近值不是严格求解。

不计算 Placidus、恒星黄道 ayanamsa、月交点、凯龙、小行星、恒星位置、次限/太阳弧/日返/月返、卜卦择时；这些有知识解释不代表有本地计算引擎。合盘以两份已验证本命数据和知识规则分析，不冒充完整组合盘计算服务。

## 紫微与奇门

本版只提供知识、访谈流程、固定解读顺序和外部盘面核验，不提供本地自动排盘 CLI。必须明确来源、流派、版本、起盘输入和时区。提供截图时使用图像读取能力，先逐字段转录让用户确认；图片看不清就说不能确认，不凭样式猜宫位。

奇门外部 JSON 可记录：`source`、`datetime`、`timezone`、`location`、`school`、`dun`、`ju`、`palaces` 与问题。九宫中的门、星、神、天地盘干必须来自盘面，不允许模型用填空方式“生成”。

紫微外部 JSON 可记录：`source`、`birth`、`calendar`、`timezone`、`school`、`palaces`、`ming`、`shen`、`sihua`、`periods`。流派四化表、闰月归属和年龄方法不一致时保留分歧而不是强制改表。

## 兼容原则

整个仓库只有一个 `SKILL.md`。五模块 references 不是五个独立 skill，不要求再加载其它技能。脚本对 Agent 宿主无强绑定，任意能读取文件/执行 Python 的工具都能使用。没有 Python 执行能力时只讲知识，不假装抽过牌或算过盘。
