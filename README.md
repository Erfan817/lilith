# 占卜师莉莉丝 · Lilith Diviner

![Lilith Diviner：复古暗黑 OVA 赛璐珞画风的中文占卜 Agent](assets/lilith-diviner.png)

> 一个隐私优先、可核验计算的中文占卜文化 AI 助手。
>
> 莉莉丝以 Agent Skill 形式安装到支持技能的 AI 宿主中，在本地计算塔罗、八字和基础占星，并对紫微斗数、奇门遁甲的可信外部盘提供有来源的解释。它不声称预测命运，也不替代医疗、法律、投资或其他现实决策。

## 产品定位与分类

**Lilith Diviner · 占卜师莉莉丝**是一款面向文化学习、娱乐与自我反思的 AI 助手，需要在能读取技能文件并执行 Python 的 AI 宿主中使用。

| 分类维度 | 定位 |
|---|---|
| 产品类别 | 中文占卜文化 AI 助手 |
| 应用领域 | 娱乐与生活方式：占卜文化、自我反思 |
| 技术形态 | Agent Skill（可安装的智能体技能） |
| 内容类别 | 塔罗、八字、星座占星，以及紫微斗数与奇门遁甲外部盘解读 |

## 为什么是 Lilith

很多占卜 Agent 会直接给出听起来确定的结论，却不说明输入、口径和未知。Lilith 把这几件事放在回答前面：

- **真实计算**：塔罗抽牌、八字历法和基础星盘由本地脚本完成，模型不手算关键结果。
- **明确边界**：未知出生时间保留范围；紫微和奇门没有本地排盘时，不伪造盘面。
- **可追溯**：参考资料、计算口径、来源状态和验证记录都保存在仓库中。
- **隐私优先**：计算默认离线，不自动上传生日；导出分享报告时默认隐藏原问题和出生资料。
- **适合反思**：回答关注象征、传统和现实行动，不把牌面或星盘包装成必然预言。

## 能做什么

| 模块 | 当前能力 | 边界 |
|---|---|---|
| 塔罗 | 78 张牌、六种牌阵、均匀无放回抽牌、正逆位、可复现实验 seed | 不自动生成原版牌图，不把牌面当作事实证据 |
| 八字 | 四柱、交节、日界、时区/DST、起运、大运、流年、未知时刻候选 | 使用 lunar-python，不是官方万年历认证；仅时辰不能推出精确起运 |
| 西方占星 | 热带黄道十天体、四轴、主要相位、整宫/等宫、未知生时当日范围 | 不计算 Placidus、恒星黄道、交点/凯龙、组合盘、次限和返照 |
| 紫微斗数 | 阅读可信外部命盘，解释宫位、主星、四化与流派设置 | 当前没有本地自动排盘 |
| 奇门遁甲 | 阅读可信外部盘，按流派和盘面解释 | 当前没有本地自动起局 |
| 本地报告 | 塔罗和基础星盘自包含 HTML/SVG 报告 | 八字和未知生时范围报告暂不支持 |

## 先看一个例子

安装完成后，可以直接对宿主说：

```text
抽三张塔罗，聊聊我和团队的分工。
帮我看太阳、月亮和上升的区别。
我只知道出生日期，不知道具体时间，能看八字吗？
```

不知道出生时间时，Lilith 会保留不确定性并追问必要资料，不会擅自把午夜或“天刚亮”当成确定钟点。

## 安装

技能目录必须叫 lilith-diviner。只选择自己使用的宿主路径，不要同时安装多份。

需要 Python 3.10 或更新版本，Python 3.14.5 也满足版本要求；命令不必叫 `python3`。已有技能 `.venv` 时优先使用其中的解释器，不必重新创建。下面的安装示例适用于首次安装。

### 找到可用的 Python

先实际运行探测，确认退出成功并输出解释器路径与版本：

```text
python -c "import json,sys; print(json.dumps({'executable': sys.executable, 'version': list(sys.version_info[:3])}))"
```

Windows 可依次检查 `python`、`py -3`、`python3`；Linux/macOS 可检查 `python3`、`python`。一个命令失败或无输出时继续检查其他候选。Windows 的 `python3` 可能只是应用商店占位程序：用 `Get-Command python,py,python3 -ErrorAction SilentlyContinue` 查路径，优先跳过指向 `Microsoft/WindowsApps` 的别名。多版本可用 Windows `py --list-paths`（旧版 `py -0p`）或 POSIX 命令发现工具查看已安装的 `python3.x`。

把下面创建环境的命令替换为已验证的启动方式，例如 `python -m venv .venv` 或 `python3.14 -m venv .venv`；带空格的绝对路径在 PowerShell 中用 `& "路径"` 调用。创建后统一使用 `.venv` 中的解释器。doctor 报依赖缺失时，只需按提示补齐技能环境，不代表 Python 不可用。

### Linux / macOS

```bash
git clone https://github.com/Erfan817/lilith-diviner.git ~/.agents/skills/lilith-diviner
cd ~/.agents/skills/lilith-diviner
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/lilith.py doctor
```

### Windows PowerShell

```powershell
git clone https://github.com/Erfan817/lilith-diviner.git "$HOME/.agents/skills/lilith-diviner"
Set-Location "$HOME/.agents/skills/lilith-diviner"
python -m venv .venv
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/lilith.py doctor
```

如果 `python` 不可用，再尝试 `py -3 -m venv .venv`。不要用没有输出的 `python3` 应用商店占位别名判断 Python 不存在。

也可以安装到 Claude Code、Cursor 或 Hermes 使用的技能目录。宿主的发现路径、工具名称和审批规则不同；当前真实多轮流程已验证 Hermes，Claude Code 和 Cursor 仍需要在各自环境中单独验收。

塔罗只依赖 Python 标准库。八字和占星需要 requirements.txt 中的固定版本依赖。doctor 只检查当前解释器，不会自动安装或修改宿主环境。

## 命令行示例

以下命令都使用技能自己的虚拟环境解释器。

```bash
.venv/bin/python scripts/lilith.py tarot --spread three --seed 42
.venv/bin/python scripts/lilith.py bazi --solar 1990-05-15 --hour 12:00 --sex 男 --as-of 2026-10-08
.venv/bin/python scripts/lilith.py astrology --datetime 2000-01-01T20:00:00 --timezone Asia/Shanghai --lat 39.9 --lon 116.4 --houses whole-sign
```

Windows PowerShell 把 .venv/bin/python 替换为 .venv/Scripts/python.exe 即可。

报告在 POSIX 系统使用 0600 权限；Windows 的隐私取决于父目录和文件 ACL，不由 Python 的数字 mode 保证。请选择仅本人可访问的目录，并在分享前预览。

### 隐私输入

塔罗通常不需要把问题传给程序。如果必须传入，使用宿主的文件工具写入私密 UTF-8 临时文件，再调用 --question-file；不要把用户原问题拼进 shell 字符串。默认 JSON 不回显原问题，--echo-question 只有在用户明确同意时才使用。会话日志和临时文件仍可能留痕，不能承诺绝对零留痕。

### 导出本地报告

```bash
mkdir -p private
.venv/bin/python scripts/lilith.py report --input examples/tarot-seeded.json --output private/tarot.html
```

分享前请打开报告预览。即使隐藏了原始生日和地点，派生星盘仍可能反推出部分个人信息；--private 会把完整原始 JSON 放入报告，只适合私下保存。

## 验证与工程状态

- GitHub Actions 覆盖 Ubuntu 和 Windows，以及 Python 3.10、3.12、3.13。
- 回归测试覆盖日期边界、时区/DST、输入校验、报告注入、路径安全和来源契约。
- scripts/validate.py 检查 Skill 元数据、参考目录、来源清单和统计文件。
- scripts/check_evals.py 检查评测数据完整性；它不冒充模型质量或占卜准确率测试。
- 真实 Hermes 多轮记录验证了自然语言发现、资料追问、未知时刻降级、修正后重算和分享报告流程；解读质量仍在持续评估。

开发验收：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests scripts/vendor/bazi/test_pai_pan.py -q
python scripts/validate.py
python scripts/update_stats.py --check
python scripts/check_evals.py
```

## 发布路线

按照下面的顺序推进，比先做宣传素材更稳：

1. **冻结产品定位**：明确“本地计算 + 有来源解读 + 现实反思”，把紫微/奇门外部盘和暂不支持的报告类型写清楚。
2. **修好第一次使用**：处理 Windows UTF-8、统一虚拟环境命令，补齐安装失败时的诊断和恢复提示。
3. **完成宿主验收**：先把 Hermes 作为正式支持对象，再分别验证 Claude Code 和 Cursor；没有实测的宿主只写“未验证”。
4. **建立发布基线**：增加 CHANGELOG、贡献指南、Issue 模板和安全报告入口，固定依赖和版本，创建 Git tag 与 GitHub Release。
5. **补齐证据**：用最终版本重新跑一组小而真实的解读评测，公开计算正确性、边界处理和已知失败，不宣传预测准确率。
6. **制作宣传入口**：README 顶部放一句话定位、30 秒安装、一次完整对话、报告截图和支持矩阵，再准备视频或图文演示。
7. **小范围发布**：先邀请少量用户试用，记录安装失败、误触发、追问质量和报告分享问题，再决定是否扩大传播。

## 资料与边界

参考资料按“作品存在、实际读到的范围、可支持的事实主张”分开记录。来源清单中包含正文已读、部分阅读、仅元数据、阻断和失败等状态；书目数量不等于全部正文已读，也不等于独立预测证据。

本项目适合文化学习、娱乐和自我反思。它不用于医疗诊断、法律意见、投资建议、录取判断、死亡预测或其他高风险决定。现实事实、专业意见和用户自己的选择优先于任何象征解释。

## 参与项目

欢迎提交能复现的问题、跨宿主测试结果、参考来源修订和更清晰的中文表达。请不要提交真实出生资料、私人对话、密钥或个人报告。

代码和原创整理采用 MIT；第三方组件、参考资料和封面素材的权利与署名要求见 NOTICE.md 和 LICENSES/。

## 相关文档

- Skill 入口与对话协议：SKILL.md
- 报告说明：docs/reporting.md
- 来源与验证规范：docs/validation-spec.md
- 八字口径与来源审计：docs/bazi-reference-audit.md
- 真实宿主流程记录：evals/results/host-v0.2.1/summary.json
- 合成示例：examples/README.md
