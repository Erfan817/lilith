# 可选本地报告

统一命令 `python scripts/lilith.py report --input <真实计算JSON> --output <本地HTML>`。只有用户要求导出时才保存；目录推荐已忽略的 `private/`、`reports/` 或仓库外目录。父目录需存在。

## 已实现

- 六种塔罗牌阵的SVG示意牌框、真实牌名/牌位/正逆位；不是原版塔罗插画，不含自动解读。
- 基础热带十天体星盘SVG和数值表；只显示输入中已计算的角点和整宫/等宫宫位，不能补造数据。
- HTML自包含，禁用脚本、联网和外部图片/CDN；适合本地打开或打印成PDF。

八字报告和未知生时当日范围报告暂不支持，会明确退出2，不画伪造的单一星盘。

## 隐私与写入

默认分享版采用允许字段投影，不展示原问题、出生日期/时刻/经纬度、任意备注。未知warning以固定提示替代，防止备注夹带私密内容。星盘派生坐标可能反推时间地点，**隐藏原始字段不等于匿名**；分享前预览并取得当事人同意。

`--private` 明确允许整个原始JSON进入报告，只能私下保存。报告拒绝写项目源码目录、覆盖输入、符号链接输出；已有文件只有 `--overwrite` 才替换。POSIX文件权限0600；Windows权限依赖目录与文件ACL，Python的mode不是私密保证。本机不是Windows，新增windows-latest CI真实运行报告功能与安全回归；此CI不认证任意用户目录的ACL配置。

最多读取1MiB JSON，拒重复key、非有限数、深层/超大结构、错误牌名/宫位/坐标。所有文本转义，输出不是可执行输入。硬链接原子发布在不支持的文件系统会干净报错，不绕过保护。

## 演示

```text
python scripts/lilith.py report --input examples/tarot-seeded.json --output private/tarot.html
python scripts/lilith.py report --input examples/astrology-j2000.json --output private/astrology.html
```

示例是合成资料。测试入口 `python -m pytest tests/test_report.py tests/test_cli.py -q`，覆盖真实计算JSON、共享隐私、SVG坐标、注入、覆写与坏输入。运行通过只验证渲染行为，不证明占卜预测效力。
