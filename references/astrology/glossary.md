# 占星术语索引：中文、英文与容易混淆的含义

> 术语表是阅读入口，不是命断词典。每个技术名只表示一种对象或规则，不能因学会名称便宣称已完成计算。译名存在地区和流派差异，本文件优先保留英文以便复核；“星座”“宫”“星”“推运”等中文字尤其需要结合上下文。

## 分类索引表

| 索引 | 主题 | 快速辨认 | 对应知识入口 |
| --- | --- | --- | --- |
| [A](#coordinates) | 坐标、时制与历法 | sign与constellation；黄经、黄纬、赤纬；UTC、JD | [天文与计算](astronomy-and-calculation.md) |
| [B](#natal) | 本命盘基本结构 | 四轴、宫位、相位、交点、顺逆行 | [基础](foundations.md)、[宫位](houses.md)、[相位](aspects.md) |
| [C](#traditional) | 传统状态与主宰 | 昼夜、尊贵、接纳、福点、时主 | [传统技术](traditional-techniques.md)、[尊贵](dignities.md) |
| [D](#relationship) | 关系盘 | 比较盘、组合中点盘、戴维森盘、双向落宫 | [关系占星](synastry.md) |
| [E](#timing) | 时间方法与问题盘 | 行运、次限、太阳弧、返照、岁限、择时、卜卦 | [时间技术](timing.md) |
| [F](#schools) | 印度概念、流派与额外因素 | ayanamsa、nakshatra、dasha、paran、小天体 | [流派历史](schools-and-history.md)、[传统技术](traditional-techniques.md) |

<a id="coordinates"></a>
## A．坐标、时制与历法

| 中文及常见别译 | 英文／缩写 | 本文件中的含义与边界 |
| --- | --- | --- |
| 黄道 | Ecliptic | 天球上的参考大圆；不是十二个天文星座的边界线 |
| 黄道星座 | Zodiac sign / Sign | 黄道十二等分中的一段；通常每段30°，不是IAU天区 |
| 天文星座 | Constellation | 按天文学边界定义的天区；不能拿它替换等分星座 |
| 热带黄道／回归黄道 | Tropical zodiac | 以春分点定义白羊起点的黄道体系 |
| 恒星黄道 | Sidereal zodiac | 以所选恒星参考起点定义的黄道，仍需指明方案 |
| 岁差 | Precession | 参考方向的缓慢变化；不是所有星座突然被官方改名 |
| 黄经 | Ecliptic longitude / λ | 沿黄道的角坐标；相位通常使用这类角差 |
| 黄纬 | Ecliptic latitude / β | 相对黄道的南北角度；不同于赤纬 |
| 绝对黄经 | Absolute longitude | 一圈0°至不足360°的数值，不只星座内度数 |
| 赤经 | Right ascension / RA / α | 赤道坐标的方向量，常用时分秒，注意与角度单位转换 |
| 赤纬 | Declination / δ | 相对天赤道的南北角度，不是黄纬，也不是地理纬度 |
| 高度角 | Altitude | 天体相对当地地平线的高度；与黄道宫位数字不同 |
| 方位角 | Azimuth | 地平坐标中的水平方向量，需要声明起点与顺序 |
| 历元 | Epoch | 模型或坐标参考时刻；不能忽略后直接比较不同时代的星表 |
| 分点 | Equinox | 坐标参考方向的标记，与历元有关但并非同一术语 |
| 地心 | Geocentric | 以地球中心为参考；不主张地球为宇宙物理中心 |
| 站心／地表观测者中心 | Topocentric | 以地表观测者位置为参考，月亮视差尤其值得注意 |
| 日心 | Heliocentric | 以太阳为参考；不等于传统所谓日心尊贵状态cazimi |
| 视差 | Parallax | 观测者位置不同造成的视方向变化 |
| 视位置 | Apparent position | 含特定观测修正的位置，具体定义需依库说明 |
| 星历 | Ephemeris | 随时间提供位置的模型或表格；不是整套解读软件 |
| 角分／角秒 | Arcminute / Arcsecond | 角度的细分单位，不是时钟分钟和秒 |
| 时区 | Time zone | 地方时制规则，IANA名称不同于固定UTC偏移 |
| 夏令时 | Daylight saving time / DST | 当地历史时制中的钟表调整，不能按现行规则反推全部年份 |
| 协调世界时 | Coordinated Universal Time / UTC | 现代常用统一时间基准，不是当地标准时 |
| 世界时一 | Universal Time 1 / UT1 | 与地球自转有关的时间尺度 |
| 地球时 | Terrestrial Time / TT | 星历动力学相关的均匀时标之一 |
| ΔT | Delta T | 通常为TT与UT1之差，不是时区或DST偏移 |
| 恒星时 | Sidereal time | 描述地球相对参考方向转向的量，不是恒星黄道的别名 |
| 儒略日／儒略日期 | Julian day / Julian date / JD | 连续天数与分数；不能与儒略历混同 |
| 儒略历 | Julian calendar | 历史年月日组织规则，不是JD数值本身 |
| 公历／格里高利历 | Gregorian calendar | 现代常用民用历法；历史改历应按地区核对 |
| 农历／阴阳合历 | Chinese lunisolar calendar | 包含月相与太阳季节配合的历法；需保留闰月信息 |

<a id="natal"></a>
## B．本命结构与相位

| 中文及常见别译 | 英文／缩写 | 本文件中的含义与边界 |
| --- | --- | --- |
| 本命盘／出生盘 | Natal chart / Radix | 以出生时刻及地点为基准的盘；未知时刻须降级 |
| 盘主／当事人 | Native | 被研究出生盘的本人，不表示其身份由盘决定 |
| 上升／升点 | Ascendant / ASC | 黄道与当地东方地平线的相关交点，不是太阳星座 |
| 下降／降点 | Descendant / DSC | 与上升相对的角点 |
| 中天／天顶 | Medium Coeli / MC | 黄道与当地子午圈的相关交点；不等于头顶的几何天顶 |
| 天底／下中天 | Imum Coeli / IC | 与MC相对的角点，传统名称含不同译法 |
| 四轴／角点 | Angles | ASC、DSC、MC、IC；不是所有宫制的宫始点都与它们一致 |
| 宫位 | House / Place | 按宫制划分的领域结构，和星座不是同一个分类 |
| 宫始点／宫头 | House cusp | 宫位边界；译为宫尖不意味着物理尖角 |
| 宫制 | House system | 划分宫位的算法；不可只写“默认”而不注明名称 |
| 整宫制 | Whole sign houses | 包含上升的星座作为第一整宫，逐座推进 |
| 等宫制 | Equal houses | 常从上升度数起，每宫等分30°；MC可不等于第十宫始点 |
| 普拉西德／普拉西德斯 | Placidus | 象限宫制之一；不能以等宫冒充其结果 |
| 相位 | Aspect | 特定角度或整座关系，不是天体之间物理作用的证明 |
| 合相 | Conjunction | 常见黄经目标角0°；同座与度数合相须分别说明 |
| 六合／六分相 | Sextile | 常见黄经目标角60° |
| 刑／四分相 | Square | 常见目标角90°；不能直接推断冲突事件必然发生 |
| 拱／三分相 | Trine | 常见目标角120°；不能据此保证成功或安全 |
| 冲／对分相 | Opposition | 常见目标角180°，不是两个人必定对立 |
| 容许度／容许误差 | Orb | 偏离目标角仍被列入的阈值；不是计算误差或发生概率 |
| 入相 | Applying | 正趋向精确关系，需运动或相应规则判断 |
| 出相 | Separating | 正离开精确关系，不能只由静态左右顺序决定 |
| 精确相位 | Exact aspect | 达到约定角度的几何时刻，不等于对应现实事件时间 |
| 顺行 | Direct motion | 在所选坐标下角度随时间正向推进 |
| 逆行 | Retrograde motion | 地心视运动反向，不是天体实际倒退或个人失败 |
| 留／近停滞 | Station / Stationary | 视角速度接近零或转向；“近”需具体阈值 |
| 月球交点 | Lunar nodes | 月球轨道与黄道交线的点，不是实体天体 |
| 平交点／真交点 | Mean node / True node | 不同模型定义的交点位置，需明确不能混用 |
| 北交／南交 | North node / South node | 升交点与降交点的常用占星名称；不是地理南北位置 |

<a id="traditional"></a>
## C．传统状态、主宰与构造点

| 中文及常见别译 | 英文／缩写 | 本文件中的含义与边界 |
| --- | --- | --- |
| 七星／古典七星 | Seven classical planets | 日月与五颗肉眼行星的传统合称，不是天文学七颗行星 |
| 昼夜分派 | Sect | 盘与行星的昼夜条件；不能仅看钟表上午下午 |
| 昼盘／夜盘 | Day chart / Night chart | 以太阳相对当地地平线判定的常见盘条件 |
| 天然吉星／天然凶星 | Benefic / Malefic | 历史功能分类，不是人的道德评价或事件保证 |
| 本质尊贵 | Essential dignity | 星座身份条件，包括本垣、擢升等传统类别 |
| 偶然尊贵／境遇强度 | Accidental dignity | 宫位、速度、可见性等条件；强不等于善 |
| 本垣／入庙 | Domicile | 行星处于其守护星座的传统身份 |
| 擢升／旺 | Exaltation | 另一种尊贵关系，不应把它自动等同本垣 |
| 失势／落陷 | Detriment | 通常与本垣相对的位置；注意中文“落陷”有歧义 |
| 落／弱 | Fall | 通常与擢升相对；需用英文区分detriment |
| 三分性 | Triplicity | 按元素三座相关的尊贵体系，可有昼夜主星差别 |
| 界 | Terms / Bounds | 星座内不等长区段及其主星，有不同表格 |
| 面／十度区间 | Face / Decan | 常见十度划分与主星规则，不能代替界 |
| 游离 | Peregrine | 在采用的表格下缺少本质尊贵，不表示没有价值 |
| 宫主星 | House ruler | 所选宫制下宫界或整宫星座的守护星 |
| 定位星 | Dispositor | 行星所在星座的守护星，不一定等于命主星 |
| 命主星／上升主星 | Ascendant ruler / Chart ruler | 常指上升星座守护星；若某流派另有定义需明示 |
| 接纳 | Reception | 某星处于另一星尊贵范围的技术关系，部分传统还要求相位 |
| 互容 | Mutual reception | 双向尊贵主宰关系，不能只理解为人际接纳 |
| 日光下 | Under the beams | 与太阳距离及可见性有关的传统状态，阈值需声明 |
| 燃烧 | Combustion | 靠近太阳的传统不利状态，不是天体真的燃烧 |
| 日心／日心尊贵 | Cazimi | 紧近太阳中心的传统状态，不是heliocentric坐标 |
| 不相见 | Aversion | 某套整座规则中缺少标准见证关系，不是没有任何几何联系 |
| 点／虚点／阿拉伯点 | Lot / Part / Arabic part | 按角度构造的数学点；若干技术早于阿拉伯语传承 |
| 福点 | Lot of Fortune / Fortuna | 由上升、日月构造，昼夜是否反转须注明 |
| 精神点 | Lot of Spirit | 另一构造点，不能直接等同福点对冲 |
| 时主 | Time-lord / Chronocrator | 分期体系中某阶段的统摄星，不是钟表小时主星 |

<a id="relationship"></a>
## D．关系盘

| 中文及常见别译 | 英文／缩写 | 本文件中的含义与边界 |
| --- | --- | --- |
| 比较盘／相互盘 | Synastry | 比较两张原盘的跨盘接触，保留双方各自坐标 |
| 组合中点盘 | Composite chart | 对同类因素取环形中点的人工盘，通常无唯一真实天空时刻 |
| 中点 | Midpoint | 环形坐标的中点，短弧与长弧分支须区分 |
| 戴维森关系盘／时空盘 | Davison relationship chart | 先求出生时空中点，再计算该时刻与地点的天空 |
| 双盘轮 | Bi-wheel | 两组坐标的展示形式，不独立定义一种解释技术 |
| 落宫／叠宫 | House overlay | 一方因素落入另一方宫位，需双向分别讨论 |
| 跨盘相位 | Inter-chart aspect | 两张盘因素间的关系；不能与盘内相位混成一条记录 |
| 生时校正 | Rectification | 根据资料和事件研究候选出生时间，不是无误差找回真实时刻 |

<a id="timing"></a>
## E．时间方法与问题盘

| 中文及常见别译 | 英文／缩写 | 本文件中的含义与边界 |
| --- | --- | --- |
| 行运 | Transit | 目标时刻实际天空对本命等基准的关系 |
| 推运 | Progression | 符号时间映射的总称，不能默认所有方法相同 |
| 次限／二级推运 | Secondary progression | 常用出生后一日象征生命一年，各星按映射日星历推进 |
| 方向法 | Direction | 一组符号或日周运动相关技术的统称，需具体方法名 |
| 太阳弧 | Solar arc / SA | 把指定太阳推进弧应用到本命因素的方向法 |
| 主限 | Primary direction | 基于日周运动等复杂约定的传统方向法，不等于次限 |
| 时间键 | Key | 符号角度或运动与生命时间的换算约定 |
| 返照／回归盘 | Return chart | 天体回到本命指定位置时立盘，不等于生日整点盘 |
| 太阳返照／日返 | Solar return / SR | 太阳回到指定黄经的实际时刻及盘 |
| 月亮返照／月返 | Lunar return / LR | 月亮回到指定黄经，不能与新月、满月混同 |
| 年度岁限 | Annual profection | 常用每周岁推进一个整座的激活规则 |
| 年主星 | Lord of the year | 在指定岁限等体系下统摄该年的行星，须注明来源规则 |
| 黄道释放 | Zodiacal releasing / ZR | 从所选点和星座周期分期的传统技术，含多层级与特例 |
| 法达 | Firdaria | 中世纪分期体系之一，不能直接套岁限或dasha规则 |
| 行星日／行星时 | Planetary day / Planetary hour | 常从日出开始，昼夜各十二段，通常不等于固定钟表小时 |
| 择时 | Electional astrology | 为明确行动在可行候选中选择时刻，不是保证吉祥的通用日期 |
| 卜卦占星 | Horary astrology | 针对具体问题立问题盘，不是本命推运或塔罗抽牌 |
| 始事盘／起始盘 | Inception chart | 为一个实际开始事件立盘，不必是通过择时挑出的时刻 |
| 入座／入宫天象 | Ingress | 天体进入所定义星座；英文语境需与普通落宫区别 |

<a id="schools"></a>
## F．印度概念、流派与额外因素

| 中文及常见别译 | 英文／缩写 | 本文件中的含义与边界 |
| --- | --- | --- |
| 印度占星／吠陀占星 | Indian astrology / Jyotish | 多传承实践的合称，不只是恒星坐标转换 |
| 岁差差值／恒星黄道偏移 | Ayanamsa / Ayanamsha | 热带与所选恒星起点的角差，需要日期与方案 |
| 月宿／二十七宿 | Nakshatra | 常用恒星黄道的二十七分段，不等于中国二十八宿 |
| 宿分／宿足 | Pada | 常用每宿四分段，不是西方四元素分类 |
| 分期／印度星限 | Dasha / Daśā | 多种主期体系的合称，不能默认为一种算法 |
| 主期 | Mahadasha | 某dasha的较大层级，需说明周期规则 |
| 子期 | Antardasha / Bhukti | 主期下的分期层级，不能忽略起始余额 |
| 罗喉／计都 | Rahu / Ketu | 印度九曜中的月球北交、南交概念，不是实体行星 |
| 分盘 | Divisional chart / Varga | 印度传统的细分结构，不等于把十二宫任意切小 |
| 心理占星 | Psychological astrology | 以动机、象征和成长为重点的解释取向，不是临床心理测验 |
| 世俗占星 | Mundane astrology | 国家、组织与公共世界的占星，不能输出灾害预警或金融定论 |
| 赤纬平行 | Parallel of declination | 同侧、近同赤纬的关系，不是黄经合相 |
| 赤纬反平行 | Contra-parallel / Contraparallel | 南北相反、赤纬绝对值接近，不是黄经对冲 |
| 同升／角点同时关系 | Paran / Paranatellonta | 当地同时升落或成为角点的关系，不等于赤纬平行 |
| 恒星 | Fixed star | 传统名称，不表示其坐标永远不变；须带星表与历元 |
| 小行星 | Asteroid | 实际小天体类别，需编号与星历，不由神话名直接推断作用 |
| 凯龙星 | Chiron | 实际小天体的占星名称，不在传统七星体系内 |
| 莉莉丝／黑月 | Lilith / Black Moon | 可能指不同月球远地点模型或小行星，必须具体标识 |
| 假想天体 | Hypothetical body | 某些体系的计算因素，不得写成已被确认的真实行星 |

## 使用术语时的校验习惯

先标识对象，再写关系，最后才讨论解释。例如“行运土星对本命太阳的黄经刑相”已经明确两张时间层；“太阳土星不好”却没有对象、角度、方向或条件。软件字段也应保持这种区分，不以一个中文总称覆盖日返、太阳弧、比较盘与本命盘。

同一译名出现歧义时，保留英文最有效。“天顶”在占星文本里常指MC，在球面天文学里zenith才是观测者正上方；“落陷”可能被用来翻译detriment或fall；“日心”可能指cazimi状态，也可能指heliocentric中心。遇到这些词，先询问文本定义，不根据中文表面一致就合并算法。

印度dasha、西方时主与中文“大运”可在文化比较中并列，但不能因都谈时间阶段就替换周期公式。福点、交点与恒星也都可能被叫“星盘点”，却分别是构造点、轨道几何点和实体天体。正确命名使读者知道哪些是测量或模型坐标，哪些是约定运算。

索引链接只是知识导航，不表示对应功能已由脚本执行。凡是没有明确计算结果、配置和测试记录的高级术语，报告应标注“概念说明”而不是“已计算”。不能把术语表的项目数量转成覆盖度营销，更不能用难懂的名称让用户误以为预测已经获证实。

## 来源与阅读说明

本表按照已读取来源的定义独立编排中文解释，未逐条翻译或复制词条。索引与边界提示为本项目原创整理。

- Skyscript Glossary：术语栏目及相关定义。https://www.skyscript.co.uk/gl/glossary.html
- Skyscript Glossary C：黄经、黄纬与迦勒底顺序。https://skyscript.co.uk/glossary/C
- Skyscript, Sect。https://www.skyscript.co.uk/glossary/sect/
- Skyscript, Declination。https://skyscript.co.uk/glossary/declination/
- Skyscript, Paran。https://www.skyscript.co.uk/glossary/paran/
- AstroWiki, Secondary Progression。https://www.astro.com/astrowiki/en/Secondary_Progression
- AstroWiki, Solar Arc。https://www.astro.com/astrowiki/en/Solar_Arc
- AstroWiki, Nakshatra。https://www.astro.com/astrowiki/en/Nakshatra
- Chris Brennan, Annual Profections, Lots, and Zodiacal Releasing。https://www.astro.com/astrology/tma_article190314_e.htm
- IANA, Time zone and daylight saving time data。https://iana.org/time-zones/tz-link
- AstroCepheus, Parallels / Contra-Parallels：仅采用几何定义。https://www.astrocepheus.com/knowledgebase/articles/parallels-contra-parallels-declination-aspects-in-astrology
