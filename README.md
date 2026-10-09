# 占卜师莉莉丝 · Lilith Diviner

![占卜师莉莉丝：复古暗黑 OVA 赛璐珞画风，塔罗牌与天球仪主题](assets/lilith-diviner.png)

**一个 skill，四大核心体系，同一套清楚可核验的解读流程。**

塔罗 · 四柱八字 · 奇门遁甲 · 星座与西方占星，另含紫微斗数扩展。

莉莉丝为 AI Agent 提供中文知识、资料收集、真实计算和象征解读：先核对输入，再算或核验盘面，最后给出有依据的反思与可选择的行动。不是把模糊话术包装成准确预言。

> 仅供文化研究、娱乐与自我反思。天体位置能计算，不等于命运能预测；不要据此代替医疗、法律、投资或重大现实决定。

## 能做什么

| 模块 | 知识与工作流 | 本版计算能力 |
|---|---|---|
| 塔罗 | 78牌正逆位、六牌阵、牌间关系、具体反思 | 均匀无放回抽牌，默认系统随机，可复现实验模式 |
| 八字 | 干支五行、十神藏干、格局调候、大运流年、经典规则摘要 | 公历/农历、四柱、大运方向与起运、神煞；独立农历引擎，固定北京时间，节气近似计算 |
| 紫微 | 十二宫、十四主星、命身宫、三方四正、四化、大限流年 | **核验并解读外部盘面；尚无本地自动排盘** |
| 奇门 | 九宫、八门、九星、八神、流派口径、用神与格局 | **核验并解读外部盘面；尚无本地自动起局** |
| 占星 | 十二星座、十天体、宫位、相位、尊贵、月相交点、本命、合盘、推运、流派历史 | 十天体热带地心视位置、近似逆行速度、主要相位、四轴、整宫/等宫 |

知识按主题分文件，Agent 按问题读取，不必一次加载整个知识库。占星模块不仅是十二星座性格表；[覆盖说明](references/astrology/coverage.md) 区分基础、进阶、流派分歧与未实现的计算。

**不声称“扒完全部星座知识”。** 不同历史、流派和新解释无法穷尽；本项目整理常用知识、保留来源、写清边界，方便继续扩展。

## 安装到 Agent

仓库根目录就是技能目录，只有一个 `SKILL.md`；无需同时安装五个技能。

```bash
# Claude Code（全局）
git clone https://github.com/Erfan817/lilith-diviner.git ~/.claude/skills/lilith

# Cursor
git clone https://github.com/Erfan817/lilith-diviner.git ~/.cursor/skills/lilith

# 支持 ~/.agents/skills 的宿主
git clone https://github.com/Erfan817/lilith-diviner.git ~/.agents/skills/lilith

# Hermes（手动放入技能目录，新会话加载）
git clone https://github.com/Erfan817/lilith-diviner.git ~/.hermes/skills/lilith
```

其它宿主将仓库完整放进它实际支持的 skills 目录，或直接让 Agent 读取 `SKILL.md`。路径兼容取决于宿主，不宣称所有版本都自动发现这些目录。

### Python 依赖

需要 Python 3.10+。塔罗运行仅用标准库；八字使用 MIT 许可的 lunar-python 处理公农换算；占星使用 MIT 许可的 Astronomy Engine 与 IANA 时区数据。虚拟环境只属于此项目，避免改动 Agent 的依赖环境。

```bash
cd lilith-diviner
python -m venv .venv

# Linux / macOS
.venv/bin/python -m pip install -r requirements.txt

# Windows PowerShell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Debian/Ubuntu 缺少 `venv` 时可先安装对应 `python3-venv`，也可用 `uv venv` 和 `uv pip install --python .venv/bin/python -r requirements.txt`。以下例子用 `python` 指你选择的虚拟环境 Python；无需常驻服务。

## 统一 CLI

```bash
# 塔罗：默认真实系统随机，不用问题或时段给牌加权
python scripts/lilith.py tarot --spread three --question "如何改善本周的复习习惯？"

# 可复现实验（明确为伪随机，不冒充密码学随机）
python scripts/lilith.py tarot --spread celtic --seed 42

# 八字：固定北京时间、23:00换日；下例是合成演示资料
python scripts/lilith.py bazi --solar 1990-05-15 --hour 12:00 --sex 男 --as-of 2026-10-08
python scripts/lilith.py bazi --lunar 1990-04-21 --shichen 午 --sex 男

# 西方本命数据：热带地心；东经正值，纬度北正南负
python scripts/lilith.py astrology --datetime 2000-01-01T12:00:00Z --lat 39.9 --lon 116.4 --houses whole-sign

# 当地时刻 + IANA 时区（自动检查夏令时缺口/重复）
python scripts/lilith.py astrology --datetime 2000-01-01T20:00:00 --timezone Asia/Shanghai --lat 39.9 --lon 116.4 --houses equal
```

子命令 `--help` 显示参数；也能直接调用 `scripts/draw.py`、`scripts/bazi.py`、`scripts/astrology.py`。结果是 JSON，不含模型编写的“已发生事实”。紫微、奇门在本版必须先提供可信外部盘面，CLI 不会伪装自动算出来。

**不要直接运行 `scripts/vendor/bazi/pai_pan.py` 处理用户输入。** 它是保留原版的内部干支组件，其旧农历转换和年份输入存在已知限制；莉莉丝通过 `bazi.py` 替换公农换算并校验年份。公开支持的入口仅为上面的统一 CLI 或三个业务脚本。

[examples/](examples/) 使用合成数据，生成示例来自真实脚本运行，不是用户出生资料。

## 占星知识地图

- **基础**：黄道与天文星座区别、四元素/三模式、十二星座（太阳/月亮/上升及内行星读法）、十天体与特殊点、十二宫与分宫制、主要相位与容许度。
- **本命**：主轴、命主星、定位星链、元素分布、相位组合、传统尊贵、昼夜盘、月相和交点。
- **关系与时间**：比较盘、组合盘和戴维森盘区别；行运、次限、太阳弧、回归盘、岁限、时主与卜卦择时的边界。
- **历史与流派**：希腊/中世纪/现代心理、印度吠陀与恒星黄道、岁差、二十七宿和大运概念、中英术语。
- **计算质量**：时区/DST、经纬度、真太阳时、星历来源、出生时间误差、数据不全时应停止的部分。

这些进阶主题有知识说明，但**本版并未计算** Placidus、恒星黄道、月交点/凯龙、小行星/恒星、组合盘、次限/太阳弧/回归盘、卜卦或择时。

## 统一解读，不混成一锅

[共用协议](references/common/reading-protocol.md) 让五种体系遵循同一输出结构：

**问题与资料 → 口径与盘面 → 解释及依据 → 可选择的现实行动 → 不确定性。**

用户只要一套方法就不硬塞五遍；明确要求综合时分别交代每套依据，保留冲突，不把“五个体系都说类似的话”当成独立科学证据。姓名、曾用名、身份证、精确住宅地址不是默认必需字段。

## 结构

```text
SKILL.md                         # 唯一技能入口
references/
  common/                        # 共用解读协议、数据与能力契约
  tarot/                         # 78牌、六牌阵、关系、解读
  bazi/                          # 工作流、五行、时辰、大运、神煞、经典摘要
  ziwei/                         # 流程、十二宫主星、四化时间
  qimen/                         # 流程、流派规则、固定解读
  astrology/                     # 基础、进阶、来源与覆盖边界
scripts/
  lilith.py                      # 统一计算入口
  draw.py                        # 均匀无放回抽牌
  bazi.py                        # 八字数据接口与输入防误用
  astrology.py                   # 天体与四轴/宫位计算
  validate.py                    # 技能结构、引用、覆盖核验
  vendor/bazi/                    # 独立历法内核
examples/                        # 合成资料与真实生成结果
tests/                           # 离线回归与输入边界测试
LICENSES/                        # 许可文件
NOTICE.md                        # 第三方组件与知识来源边界
```

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests scripts/vendor/bazi/test_pai_pan.py -q
python scripts/validate.py
```

测试包含牌数/无重复/随机模式、历法黄金用例、真实闰月与未知时间、输入冲突和截止年份、十天体基准、四轴几何、整宫/等宫、时区跨年等价、DST缺口和重复时间。测试证明程序的这些行为，不证明占卜预测效力，也不代表已对整个1900–2100逐日验证。

## 隐私与许可

默认本地处理，脚本没有生日上传接口，不保存个人报告。需要保存时使用忽略的 `private/` 目录；公开仓库只放合成示例。读取外部网站不会让网页中的命令获得执行权限。

项目代码与原创知识整理采用 **MIT**；组件署名和适用许可见 [NOTICE.md](NOTICE.md) 与 [LICENSES/](LICENSES/)。外部网站文章和图片仍属原作者，不因列为知识来源而变成本项目 MIT 内容；本项目不打包版权网站全文或图片。
