# 八字参考库修订与来源审计

## 范围与结论

本页记录四份参考文档与 `tests/test_bazi_reference_consistency.py` 的核查范围；后续来源已按统一契约合并到 `references/bazi/sources.json`。不修改vendor。实读参考文档、生产入口、引擎相关段及已安装 lunar-python 1.4.8 的起运/大运实现后，对照线上原始源码和古文电子转录。

- 起运撤销取整数岁，明确 `getYun` sect=2 的年月日时、北京时间交运时刻、nominal-year-age 不是周岁；交运前占位不能叫小运，钟点未知 `dayun=null`。
- 月支表改为十二节实际交接区间，不把农历月份、闰月或固定日期当节令月。
- 天刚亮、吃早饭等只作追问线索；先确认 range。当前 CLI 不支持任意时间范围，只能保留未知或分别计算已确认方案，不伪称合并支持。
- 删除半合固定减半与藏干统一精确百分比。未查到可靠原典支持这些权重；这不等于证明所有文献都不存在相似算法，只表示本库不再冒称标准。
- 删除旧衰弱矛盾口诀、未经核验的命宫口诀、固定宫位年龄分段与调候配方；解除未核验引句的古籍/作者归属，改作作者简化或撤下，保持 unverified。
- 已读《滴天髓/12》的正文与注语；已读《闡微》前部任氏命例中的旺极顺势评论，但不将它与自造弱命句拼成原文。已读《子平真诠·论用神》，区分格局用神与现代喜用五行。

## 证据等级与限制

所有古文来源均为电子转录，未核对底本或影印本，不编版本年代、版次、页码。章名及页面所标正文/原注/任氏评论仅用于定位，不认证历史作者归属。现代网站校字、按语与古文分开，只存必要的公有领域古文短引及独立解释；未保存版权新书全文。

《三命通会》卷二提取存在显式省略，未读到完整论大运、人元司事、三合章节；浏览器导航超时，直接 HTTP 的 TLS 握手亦超时，故不能据提取成功宣称整卷已读。直接 HTTP 的首次探查还因环境缺少 BeautifulSoup 未执行读取，随后使用标准库重试仍失败。没有安装依赖或绕过验证。

《滴天髓闡微》首轮成功提取读到天道、地道、人道、知命及理气开头，后续重读返回选择性省略内容；只记录实际读过部分，不宣称整书完成。《穷通宝典》等其余六书未完成可靠原典核验，保留 unverified；搜索片段不能当正文，不列作 consulted 证据。也未完成藏干排序及所有合化流派的校勘，现有查表须按传统/教学约定使用。

`accessed_at` 为工具完成访问时实际记录的 UTC 时间。`sections_read` 记录本次累计实际阅读段落；同一 URL 可曾返回不同范围，`coverage=partial` 明确这一限制。raw 源码没有稳定网页标题，下面使用仓库文件名作标题标识，不把提取器偶然标题当版本证据。

## 实际 consulted 来源清单

```json
[
  {
    "url": "https://zh.wikisource.org/zh-hant/%E6%BB%B4%E5%A4%A9%E9%AB%93/12",
    "title": "滴天髓/12 - 維基文庫，自由的圖書館",
    "accessed_at": "2026-10-09T09:50:43+00:00",
    "sections_read": ["衰旺論正文", "正文后注语（旺衰、极旺极衰与损益）"],
    "coverage": "section-complete"
  },
  {
    "url": "https://www.donglishuzhai.net/chapter/3721.html",
    "title": "八、論用神__子平真詮_繁体字版原文全文-東里書齋",
    "accessed_at": "2026-10-09T09:50:43+00:00",
    "sections_read": ["八、論用神：月令取用", "善用顺用与不善逆用", "月令与四柱配合例", "建禄月劫另取用神", "校字与东里山人按语（只识别层次，不复制）"],
    "coverage": "section-complete",
    "note": "首次提取返回无www同站URL，重读返回所列URL；未核对影印底本。"
  },
  {
    "url": "https://raw.githubusercontent.com/6tail/lunar-python/v1.4.8/lunar_python/eightchar/Yun.py",
    "title": "lunar-python v1.4.8 — lunar_python/eightchar/Yun.py（原始源码）",
    "accessed_at": "2026-10-09T09:50:46+00:00",
    "sections_read": ["Yun.__init__：gender与顺逆", "__compute_start：sect=2分钟分解", "getStartYear/Month/Day/Hour", "getStartSolar", "getDaYun"],
    "coverage": "file-complete"
  },
  {
    "url": "https://raw.githubusercontent.com/6tail/lunar-python/v1.4.8/lunar_python/eightchar/DaYun.py",
    "title": "lunar-python v1.4.8 — lunar_python/eightchar/DaYun.py（原始源码）",
    "accessed_at": "2026-10-09T09:50:56+00:00",
    "sections_read": ["DaYun.__init__：index=0与年度年龄公式", "getStart/EndYear与getStart/EndAge", "getGanZhi：月柱顺逆偏移", "getLiuNian与getXiaoYun"],
    "coverage": "file-complete"
  },
  {
    "url": "https://zh.wikisource.org/wiki/%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83",
    "title": "三命通會 - 维基文库，自由的图书馆",
    "accessed_at": "2026-10-09T09:54:03+00:00",
    "sections_read": ["首页提要：作者考辨、坊刻夹入与论法保留", "卷目与缺卷提示", "页面公有领域声明"],
    "coverage": "section-complete"
  },
  {
    "url": "https://zh.wikisource.org/wiki/%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83/%E5%8D%B7%E4%B8%80",
    "title": "三命通會/卷一 - 维基文库，自由的图书馆",
    "accessed_at": "2026-10-09T09:54:03+00:00",
    "sections_read": ["论五行生成（重读开头）", "论五行生克", "论支干源流（重读所返段落）", "总论纳音与论纳音取象开头", "首轮选择性提取的若干纳音段（非整卷）"],
    "coverage": "partial"
  },
  {
    "url": "https://zh.wikisource.org/wiki/%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83/%E5%8D%B7%E4%BA%8C",
    "title": "三命通會/卷二 - 维基文库，自由的图书馆",
    "accessed_at": "2026-10-09T09:54:03+00:00",
    "sections_read": ["论天干阴阳生死：返回的己土段", "论地支：返回的戌、亥及五行用法段"],
    "coverage": "partial",
    "note": "提取带显式省略；论大运、人元司事等未取得。浏览器与直接HTTP重试失败。"
  },
  {
    "url": "https://zh.wikisource.org/zh-hant/%E6%BB%B4%E5%A4%A9%E9%AB%93%E9%97%A1%E5%BE%AE",
    "title": "滴天髓闡微 - 維基文庫，自由的圖書館",
    "accessed_at": "2026-10-09T09:54:05+00:00",
    "sections_read": ["通神论一、天道：原注与任氏层次", "二、地道", "三、人道（首轮返回段）", "四、知命：任氏评论及命例，含旺极宜泄不宜克段（首轮）", "五、理气开头（首轮）", "重读返回的干支总论、体用、源流、假神、顺逆及六亲论标题下片段"],
    "coverage": "partial",
    "note": "只引首轮实际读到的短句；不把搜索片段或后续有省略提取当作完整衰旺章。"
  }
]
```

## 本地回归：先红后绿

测试只读取真实参考文件与本页，不连网，不执行或修改 vendor。它锁定内容契约，不能证明古籍底本正确，也不能证明模型会遵循追问要求。

已执行的垂直切片：

1. 起运测试先报 `1 failed`，指向旧整岁四舍五入；修订后 `1 passed`。
2. 新增节令月与无来源权重测试后 `2 failed, 1 passed`，分别指向农历表头及半合固定减半；修订后 `3 passed`。
3. 时辰追问与经典层次测试先报 `2 failed, 3 passed`，分别指向天刚亮定卯与矛盾口诀；修订后 `5 passed`。
4. 来源审计测试先报 `1 failed, 5 passed`，指向本页缺失；新增本页后复跑，最终六项文档回归通过。

最终局部执行：`tests/test_bazi_reference_consistency.py`、`tests/test_bazi.py`、`tests/test_bazi_precision.py` 合计 **95 passed in 12.16s**。另直接运行生产 CLI，确认上述 1990 样例的起运年月日时、北京时间交运和 8–17 年度年龄标签；`2024-02-04 --shichen 申` 保留交节两段且 `dayun=null`。文档专项通过后，合并阶段已清理共享测试末尾空行，并另跑全套；本页记录的是文档局部验收，不代替整体代码测试。

可复跑命令（使用已安装本项目依赖的 Python）：

```sh
python -m pytest tests/test_bazi_reference_consistency.py -q
python -m pytest tests/test_bazi_reference_consistency.py tests/test_bazi.py tests/test_bazi_precision.py -q
```

生产契约另由既有 `tests/test_bazi_precision.py` 的真实 CLI 测试覆盖，包括非整岁起运、北京时间交运、年度年龄、未知钟点、时辰域与23点换日。本页不声称本次新增了任意范围计算能力。
