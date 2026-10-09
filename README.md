# 占卜师莉莉丝 · Lilith Diviner

![占卜师莉莉丝：复古暗黑 OVA 赛璐珞画风，塔罗牌与天球仪主题](assets/lilith-diviner.png)

一个中文占卜文化与反思 Skill：塔罗、八字、星座与西方占星共用资料、真实计算和解读流程；奇门、紫微为外部盘解读扩展。莉莉丝沉静、亲近，会说清依据和不知道的部分。

仅供文化学习、娱乐与自我反思。可计算天体和历法，不意味着能预测命运；不替代医疗、法律、投资或重大现实决定。

## v0.2.1 能做什么

| 模块 | 实际能力 |
|---|---|
| 塔罗 | 78牌、六阵、均匀无放回；问题文件/标准输入，默认不回显原问题 |
| 八字 | 完整交节/四柱/起运接口，IANA时区与DST校验，明确日界；未知时刻候选；可选地方视太阳时 |
| 占星 | 热带十体、主要相位、四轴、整宫/等宫；未知生时输出当日抽样范围而非虚构本命时刻 |
| 奇门、紫微 | 解读可信外部盘，**尚无本地自动起局/排盘** |
| 使用与分享 | 环境自检，来源小批检索，塔罗/基础星盘离线HTML与SVG报告 |

[占星覆盖](references/astrology/coverage.md)区分知识和计算。

全球真实书目与历史/教学案例见[阅读规则](references/common/research-reading-guide.md)、[实验证据](references/common/experiments-and-evidence.md)与[索引](docs/library-index.json)：先分清作品存在、内容已读、事实主张三层，再讨论“可教规则”和“不能推出的结论”。合盘、行运等有知识资料，但没有双盘比较/组合盘、次限/返照接口；也不计算Placidus、恒星黄道、交点/凯龙。知识无法穷尽，不宣传“扒完全部星座知识”。

## 安装

根 `SKILL.md` 的标识与安装文件夹统一为 **`lilith-diviner`**，不要保留旧目录名 `lilith`。

```bash
# Claude Code
 git clone https://github.com/Erfan817/lilith-diviner.git ~/.claude/skills/lilith-diviner
# Cursor（以所用版本实际技能发现路径为准）
 git clone https://github.com/Erfan817/lilith-diviner.git ~/.cursor/skills/lilith-diviner
# 支持 ~/.agents/skills 的宿主
 git clone https://github.com/Erfan817/lilith-diviner.git ~/.agents/skills/lilith-diviner
# Hermes
 git clone https://github.com/Erfan817/lilith-diviner.git ~/.hermes/skills/lilith-diviner
```

只选自己的宿主路径，无需安装五个技能。旧安装先备份 `private/` 等个人文件，更新并将目录改名 `lilith-diviner`，重新创建环境；新会话加载。不要同时留两份入口。宿主工具名、权限和自动发现不同；本机没运行Claude/Cursor原生加载验收，不承诺所有版本兼容。

需要 Python 3.10+，在技能目录建独立环境：

```bash
python -m venv .venv
# Linux/macOS
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/lilith.py doctor
# Windows PowerShell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/lilith.py doctor
```

Debian/Ubuntu缺venv可安装对应python3-venv或使用uv。doctor只检查当前解释器、给建议，不擅自安装或修改宿主环境；单独塔罗只需标准库，可 `doctor --module tarot`。`doctor --module bazi` 默认检查全部功能；只需民用时可 `--feature civil`，视太阳时用 `--feature apparent-solar`（另需astronomy-engine）。以下 `python` 指已选择的环境解释器。

## 开始使用

装好后可说“抽三张塔罗，聊聊团队分工”“太阳月亮上升有什么区别”“帮我看八字”。不知道出生时间可以明确说，不必为了完整命盘编一个时刻。

命令行例子均为合成资料：

```bash
python scripts/lilith.py tarot --spread three
python scripts/lilith.py tarot --spread celtic --seed 42
python scripts/lilith.py bazi --solar 1990-05-15 --hour 12:00 --sex 男 --as-of 2026-10-08
python scripts/lilith.py bazi --solar 2024-02-04 --timezone America/New_York --hour 03:26
python scripts/lilith.py bazi --solar 2024-02-04 --hour 16:24 --time-basis apparent-solar --longitude 90
python scripts/lilith.py astrology --datetime 2000-01-01T20:00:00 --timezone Asia/Shanghai --lat 39.9 --lon 116.4 --houses whole-sign
python scripts/lilith.py astrology --date 2000-01-01 --timezone Asia/Shanghai
```

v0.2.1修正流年立春换年、功能依赖自检、八字参考口径与跨平台路径；新增Windows CI。流年`--as-of`接受日期或带UTC偏移的ISO时刻；立春日只给日期时保留前后候选，不擅自选正午。

八字默认固定UTC+8，显式IANA才处理当地历史规则；年/月交节按绝对瞬间，日/时柱按所选钟标。未知时间/仅时辰不算确定起运，23点日界保留候选。详见[八字口径](references/bazi/workflow.md)。**不要直接运行内部 vendor CLI 处理用户输入。**

塔罗通常不需要传问题。确需传入时，以宿主文件工具写私密UTF-8文件或用标准输入，再 `tarot --question-file <路径>`；不要把原问题插进shell单引号。默认不回显，`--echo-question`须明确允许。文件需用后清理；宿主日志仍可能保留输入，不能承诺零留痕。

## 地点与报告

城市候选查询是可选联网步骤：`location --query-file <仅城市国家的文件> --allow-network`，一次最多3候选，须确认同名城市；不猜时区、不发送生日。本服务器直连Nominatim验证失败，保留手动经纬度/IANA输入路径，不把联网成功当已验证。服务政策、隐私与权限须先告知，不批量调用。

要求导出时，先创建被忽略的 `private/` 目录，再运行：

```text
python scripts/lilith.py report --input examples/tarot-seeded.json --output private/tarot.html
python scripts/lilith.py report --input examples/astrology-j2000.json --output private/astrology.html
```

POSIX输出文件使用0600；Windows隐私依赖所选目录与文件ACL，不承诺mode-0600，导出前确认只有本人可访问。默认分享版隐藏原问题和生日时地；派生星盘仍可能反推个人信息，分享前预览。`--private`含原始JSON，不可公开。报告不自动写解读，八字和未知生时范围报告暂不支持。见[报告说明](docs/reporting.md)。

## 校验与评测

```text
python -m pip install -r requirements-dev.txt
python -m pytest tests scripts/vendor/bazi/test_pai_pan.py -q
python scripts/validate.py
python scripts/check_evals.py
python scripts/update_stats.py
python scripts/update_stats.py --check
python scripts/lilith.py sources --module astrology --query houses --limit 5
```

[v0.2.1修复清单](docs/v0.2.1-acceptance.md)、[验证记录](docs/verification-v0.2.1.json)与[八字来源核查](docs/bazi-reference-audit.md)说明本轮范围。

[实时统计](docs/stats.json)由扫描生成，不手改；[v0.2验证记录](docs/verification-v0.2.json)记录本机与全新环境实际结果；[来源契约](docs/validation-spec.md)保留真实阅读范围和访问精度。[评测案例](evals/evals.json)包括中文正负触发和解读断言；离线检查不证明宿主自动加载，模型新旧对照结果另存证据，不包装成占卜准确率。[真实Hermes多轮流程](evals/results/host-v0.2.1/summary.json)已运行并核对文件，解读仍有记录在案的措辞/估计问题，不能把流程通过当解释质量认证。历史docs/verification.json与content-audit.json只代表旧版本。

## 隐私与许可

计算默认离线、不上传生日、不自动保存个人报告；会话/工具日志与临时文件可能留痕。仓库只放合成示例，个人资料与密钥不进Git。代码与原创整理采用MIT，组件署名见[NOTICE](NOTICE.md)；外部文章、牌图和画风资源保留各自权利与署名。封面画风参考：**yang0** 的 [handraw-style](https://github.com/yang0/handraw-style)，并保留其附加署名许可。
