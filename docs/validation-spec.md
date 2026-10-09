# 结构、来源与统计校验

## 运行

在可安装根目录运行；根目录的最后一级名称必须与 `SKILL.md` 的 `name` 相同。

```text
python scripts/validate.py
python scripts/validate.py --generic --root path/to/example-skill
python scripts/sources.py --module astrology --query dignity --limit 5
python scripts/update_stats.py
python scripts/update_stats.py --check
```

结构验证需要开发依赖中的 PyYAML。来源检索和统计生成只依赖标准库，不联网、不修改阅读状态。

## Agent Skills 通用层

依据 [Agent Skills Specification](https://agentskills.io/specification)，不是 Hermes 仓库内部的短描述 house rule：

- 仅 `name`、`description` 为必填 frontmatter 字段。
- `name` 长度 1–64，须为小写字母/数字/连字符，不允许首尾或连续连字符；与实际安装根目录名称逐字匹配，不修复或规范化错误 token。Unicode 字母/数字的接受方式与官方 `skills-ref` 的 `isalnum` 检查一致。
- `description` 非空、长度 1–1024；不要求英文、句号或不超过 60 字。
- `compatibility` 可选，若提供须非空、长度不超过 500。
- `metadata` 可选，允许任意 string → string；`version`、`author`、平台信息应放在这里，不能是嵌套结构或非字符串。
- `license`、`allowed-tools` 为可选字符串。校验 `allowed-tools` 的类型不意味着授予工具权限；实际许可由宿主决定。
- 通用目录规范只要求根 `SKILL.md`；附带的示例/资源文件不被当作额外安装入口。通用模式不要求莉莉丝的参考资料、中文描述或特定领域覆盖。

验证器另检查非空正文、本地 Markdown 链接和脚本语法，作为项目完整性检查；只做AST语法解析，**不导入或执行待审目录中的Python脚本**。牌义覆盖使用验证器的固定词表，抽牌实现正确性由真实CLI测试另行验证。`--generic` 去掉下面的莉莉丝专属约束，但仍验证发现的 v2 来源清单。

## 莉莉丝项目层

默认 CLI 启用；Python API 使用 `audit(root, project=True)`，`audit(root)` 默认通用模式。

- 只有一个项目 `SKILL.md` 入口。
- 描述有中文领域关键词、使用/询问触发说明与“不用于”边界；这是项目要求，不是通用 Agent Skills 要求。
- `MODULE_FILES` 仅定义必需核心资料，用来检查缺失/过短文件；不充当实际资料统计总数。
- 项目模式检查塔罗牌表和十二星座覆盖；通用 fixtures 不必具备这些领域内容。

## 来源 v2 契约

六份清单使用相同结构，机器可读定义见 [source-schema.json](source-schema.json)：

```json
{
  "schema_version": 2,
  "module": "tarot",
  "documents": ["cards.md"],
  "source_policy": "只允许实际读取的范围支持知识综合。",
  "sources": [],
  "extensions": {}
}
```

上例只展示字段结构；实际清单的 `sources` 必须为非空列表。`documents` 为模块目录内的相对 Markdown 路径。运行时逐条检查所有来源，不把“JSON 非空”当作合格。

每条必填 `url`、`title`、`accessed_at`、`accessed_precision`、`retrieval`、`topics`、`use_for_synthesis`、`role`。

- `url` 必须是有主机的 HTTP(S) URL；拒绝空白、非法端口或内嵌凭据；标题为非空字符串。
- `retrieval` 包含非空 `status`、`method`、`detail`。允许状态为 `body_read`、`sections_read`、`partial_body_read`、`code_read`、`provenance_review`、`metadata_only`、`index_only`、`image_only`、`blocked`、`failed`、`excluded`。
- `topics` 为字符串列表，未知主题可保留空列表；`use_for_synthesis` 必须是布尔值，不接受 0/1 替代。
- `use_for_synthesis: true` 仅允许实际读取内容的四类状态：`body_read`、`sections_read`、`partial_body_read`、`code_read`。读取成功也不自动代表被用于综合；依赖审查、目录、失败和排除候选不能统一标成 true。
- `partial_body_read` 与完整/相关章节读取分开；具体可用范围以 `detail` 和历史备注为准，不能把局部读取升级为全文。

### 时间精度与迁移

- `instant`：`accessed_at` 是原先真实记录的有时区 ISO 时间点；校验真实日期、时分秒和时区分量。
- `date`：`accessed_at: null`，保留原 `accessed_on: YYYY-MM-DD`，并给出非空 `accessed_reason`。不得补成 UTC 午夜。
- `unknown`：`accessed_at: null`，必须给出原因，不能藏掉已知旧日期。
- 原条目、原分组和备注完整保留在 `extensions.legacy`、`extensions.legacy_group`；原清单顶层信息保留在 `extensions.legacy_manifest`。其中旧 `source_count` 等只是历史声明，不是实时统计。
- 缺仓库标题通过真实 GitHub API 获取。新增的 `extensions.metadata_retrieval` 独立记录实际查询时刻、`metadata_only` 与查询范围；这个时刻不是旧代码或文章的阅读时刻，也不能证明新读了正文。
- 失败页面无可信标题时明确使用历史失败候选/URL 标签，不能凭空补成成功取得的页面标题。
- 允许同 URL 的不同实际记录，例如先局部提取成功、后来浏览器被阻止；不合并或抹去两次结果。

## 有界检索

`scripts/sources.py` 实际扫描清单，先校验，再按 `--module` 精确筛选和 `--query` 大小写无关子串检索标题、URL、主题、角色、备注和读取范围；最后应用 `--limit`。

默认只输出 5 条，可显式选择 1–50 条；不默认输出整份来源清单。返回 `total_matches`、`returned`、`has_more` 和精简记录，包括清单相对路径/索引与读取状态。检索结果不是自动推荐或全部可靠依据，引用前核对 `use_for_synthesis` 及实际读到的范围。不要为了查一条来源把大型清单整份读进上下文。

任何清单无效都会失败并指出文件和字段，不返回貌似完整的部分成功结果。查询不存在则正常返回空列表和准确的零计数。

## 实际扫描与确定性统计

[stats.json](stats.json) 由 `scripts/update_stats.py` 生成，不能手改。来源记录数、URL 精确字符串去重数、综合证据数、状态/时间精度分布、各模块及各清单统计均由代码计算。

- `reference_files`、`astrology_topics` 是实际 Markdown 扫描数量；`required_core_*` 是项目核心要求数量。新增参考文件/模块会被纳入实际统计。
- `.git`、`.venv`、`.pytest_cache`、`__pycache__` 不参与扫描；忽略规则相对安装根应用，不因为根的祖先目录同名而忽略整项技能。
- `reference_characters` 是参考 Markdown 解码后的字符数，JSON 清单不算知识正文。
- 统计不包含生成时间、文件 mtime 或 `docs/stats.json` 自身，重复生成不会出现时间戳漂移。
- `--check` 比较确定性的完整序列化结果，缺失/陈旧返回 1，不写文件；普通生成返回 0。无效来源阻止更新，不覆盖已有结果。
- `docs/verification.json`、`docs/content-audit.json` 是历史审计，不由本生成器修改或冒充最新验证。

## 回归测试

```text
python -m pytest tests/test_validate.py tests/test_sources.py -q
python -m pytest tests -q
```

包含通用最小 fixtures、字段边界/类型、损坏 YAML、name/安装根不匹配、独立中文触发检查、来源逐字段校验、日期精度保真、重复 URL 的不同结果、真实文件检索 CLI 与确定性统计读写/陈旧检查。新增生产行为先运行红测试，再实现并重跑绿测试。
