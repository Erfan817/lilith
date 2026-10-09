# 数据与能力契约

## 塔罗 v1.1

入口 `draw.py` 或 `lilith.py tarot`。JSON有 `spread/deck/algorithm/randomness/seed/reversed_probability/cards`；每张牌 `position/card/orientation/is_major`。均匀无放回78牌、无问题/时段权重。默认 `SystemRandom`，指定seed明确是可复现实验，不是超自然证据。

自由文本支持UTF-8 `--question-file` 或 `--question-file -` 标准输入，最大65536字节。`question=null` 默认不回显，`question_provided`表示有输入；只有显式 `--echo-question` 才输出原文，可能进入宿主日志。临时文件须私密且用后清理。

## 八字

`bazi.py`校验公历/农历闰月与有界年份，`bazi_engine.py`使用lunar-python1.4.8完整交节、四柱和起运。原vendor只供规则辅助，不运行其近似compute。JSON schema1.1保留 `input/conventions/pillars/dayun/current_year/shensha/warnings` 和 `engine/uncertainty`，增加 `flow_year`；`current_ganzhi`允许null，不能把null换成公历年干支。

- 默认固定UTC+8；显式IANA时区解析民用时，DST缺口拒绝，歧义要求fold。
- 年/月、起运用绝对瞬间；日/时默认当地民用钟标，23点换日、sect1；起运sect2，运段虚岁。不是所有流派通用口径。
- 显式 `--time-basis apparent-solar --longitude`以太阳视赤经/恒星时算均时差和经度/UTC偏移修正，仅影响日/时柱。`pillar_time`是无时区钟标，不是新瞬间；原 `civil_time/calendar_time`不变，`solar_correction`记方法与版本。
- 未知钟点/只有时辰输出稳定字段和最多8个相关候选，起运null。日干不唯一时不编十神、神煞。太阳时未知钟点暂拒绝。
- 流年按立春实际交节。截止日期代表北京时间整日范围，立春当日没有截止钟点时保留前后干支；带UTC偏移的ISO截止时刻可确定一侧。默认实际当前瞬间；仅知逝世年份保留该年内且不晚于分析截止的候选，不伪造日期。`current_year`仍是公历年份标签。`flow_year.as_of_precision`只记录截止输入date/instant，`deceased_precision`记录可选逝世资料year，`domain_precision`记录最终范围精度。范围不得早于真实出生瞬间；仅时辰/未知时刻使用其真实域最早端，不代入中点；精确截止早于出生瞬间明确拒绝。
- `--place`只展示；年份1900–2100有界，逝世不早于出生、不越分析截止。输出引擎版本和来源独立校验，不承诺官方认证或所有时刻穷举。

细节见[八字口径](../bazi/workflow.md)。

## 占星

已知时间接口按UTC `[1900-01-01T00:00Z,2101-01-01T00:00Z)`统一验证；显式偏移或IANA，不混用；DST缺口/回拨明确处理。Astronomy Engine热带地心日期视坐标十体，不是Swiss Ephemeris。经纬度同时给才算四轴、整宫/等宫；前后0.05日差分估速度，主要合/六/刑/拱/冲相位，不精确求留点/入出相。

`--date YYYY-MM-DD --timezone IANA`是未知时刻降级：`mode=unknown-time-day-range,time_known=false`，`bodies/angles/houses/aspects=null`，`body_ranges`给97点抽样的首末黄经、相对首点范围和sampled_signs。日期采用当地午夜半开区间，末端样本仅用于包络；不能把任一样本当出生时刻，也不宣称完整误差条带或精确换座搜索。午夜本身不存在/歧义时明确失败，不猜日界。

不实现Placidus、恒星黄道、交点/凯龙、组合盘、次限、返照、双盘接触或行运精确搜索。合盘和时间技术文档只用于阅读外部可靠数据。完整[覆盖说明](../astrology/coverage.md)。

## 奇门与紫微

本版只有知识、访谈流程和外部盘核验，不提供本地自动排盘。输入需盘面来源、版本、流派、原时间/历法与设置。截图逐字段读取确认，看不清就说不能确认，不猜。

奇门记录 `source/datetime/timezone/location/school/dun/ju/palaces/question`；九宫门星神、天地盘干来自真实结果。紫微记录 `source/birth/calendar/timezone/school/palaces/ming/shen/sihua/periods`；闰月、四化、年龄法分歧保留。

## 工具与报告

`doctor`只检查调用它的解释器，不安装或联网。`sources`按module/query小批返回、默认5条，清单无效整体失败。统计由扫描生成，不靠手写。

`report`读取真实计算JSON，输出离线SVG/HTML；当前仅塔罗和已知时刻基础占星。默认去原问题、出生时地与任意备注，未知warning换固定提示；派生结果仍可能反推，不能承诺匿名。显式private保留原JSON，不可公开。八字和未知时刻范围报告拒绝而非补造。

`location`只在显式allow-network后发送城市查询、最多3候选，需要用户确认；时区仍需独立核验。当前服务器真实直连查询失败，不以模拟HTTP测试冒充成功。所有计算和报告默认离线。

## 兼容

只有一个根 `SKILL.md`；安装目录与name同为`lilith-diviner`。命令由实际宿主执行工具调用，不强制Hermes语法。没有执行能力只能知识解释，不能表演抽牌/排盘；权限和真正自动加载仍由宿主决定。
