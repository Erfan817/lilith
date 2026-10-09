# Notices and source boundaries

## Project authorship

Lilith / 莉莉丝 is maintained by Erfan (Erfan817). The unified workflow, CLI wrappers, tarot sampling engine, astronomical chart integration and original Chinese reference synthesis are project work. Contributions do not erase existing component copyrights.

## BaZi calendar component

Files under `scripts/vendor/bazi/` and the five table/summary files in `references/bazi/` (other than `workflow.md`) derive from jinchenma94/bazi-skill, revision `112a5d84cd1a001a0038cafca3be68d93e4c0cc9`, licensed MIT.

Copyright (c) 2025 jinchenma94. Full notice is retained in `LICENSES/bazi-skill-MIT.txt`; exact imported file hashes are recorded in `docs/bazi-import.json`. The calendar is integrated through the project's JSON/input-validation layer, not exposed as a second skill entry. Its approximations and known scope restrictions are stated in the interface and workflow. The unchanged raw vendor CLI is an internal component, not a supported user entry: its old lunar conversion and unbounded year path are bypassed or validated by `scripts/bazi.py`.

## Lunar calendar dependency

`lunar-python==1.4.8`, https://github.com/6tail/lunar-python , is an MIT-licensed dependency by 6tail. It supplies production civil-date lunar/solar conversion; the integrated wrapper deliberately bypasses the legacy calendar component's lunar conversion. Full notice is retained in `LICENSES/lunar-python-MIT.txt`. The package is installed, not vendored.

## Astronomy Engine dependency

`astronomy-engine==2.1.19` is a separate MIT-licensed dependency by Don Cross, https://github.com/cosinekitty/astronomy . Its full MIT license is retained in `LICENSES/astronomy-engine-MIT.txt`. It is installed as a package, not vendored. Accurate astronomical coordinates do not substantiate astrological predictions.

## Time zone data

`tzdata==2025.2` supplies IANA time zone records through Python's `zoneinfo` when system data is absent. The Python tzdata distribution and IANA data keep their original upstream notices; this dependency is not relicensed by Lilith and is not bundled in the repository.

## Reference material

Source inventories in `references/*/sources*.json` identify material actually consulted, retrieval outcomes, and the intended topics. Chinese newly written synthesis is project content; cited source articles, book translations, diagrams and images keep their authors' rights. No permission to redistribute an entire website, its media, or a modern copyrighted book is implied.

Publicly viewable repositories without an explicit redistribution license are not copied into this repository. General historical concepts and independently expressed rules may be discussed, but their original source-specific code and wording are not relicensed or reproduced.

## Cover artwork and style reference

`assets/lilith-diviner.png` is an AI-generated character illustration produced for this project through Packy's OpenAI-compatible Images API, using `gpt-image-2` at high quality. It is the actual generated output, not an image copied from a gallery. The cover does not depict a real person or reproduce a gallery character.

The rendering guidance was informed by **yang0**, https://github.com/yang0/handraw-style , revision `4eb29e2fcea3d9595d2f67b363e30ffdea338027`. Legacy style `239` maps to `FG-001`, “Late-80s Cyberpunk Dark OVA Cel Anime”. The gallery's custom **MIT License (with Attribution Requirement)** is retained in `LICENSES/handraw-style-attribution.txt`; it is not plain unmodified MIT. No gallery sample is redistributed. Artwork provenance is documented in `assets/README.md`; API credentials and server configuration are excluded from this repository.

## Scope

MIT covers the project's work subject to the retained component notices above. Examples contain synthetic inputs. No user birth records, credentials, private conversations or personal reports belong in the public repository.
