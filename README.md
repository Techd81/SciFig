<details open>
<summary><b>English</b> | <a href="#中文">中文</a></summary>

# SciFig Generate Skill

A reusable agent skill that transforms CSV, Excel, or matrix-style experimental data into publication-ready scientific figures with journal-style defaults, statistical guardrails, rendered QA, and reproducible export plans.

## Install

```bash
git clone https://github.com/Techd81/SciFig.git
cp -r SciFig/.claude/skills/scifig-generate ~/.claude/skills/
```

## What It Does

- Validates real data paths before reading files
- Detects tidy, wide, and matrix data plus scientific domain cues
- Recommends 115 implemented publication-grade chart types across 13 domains
- Generates Nature/Cell/Science/Lancet/NEJM/JAMA-aligned figure code
- Applies adaptive visual-density, palette, legend, layout, and performance policies
- Uses optional read-only agents for schema, chart/stat, layout, palette, code, and rendered QA gates
- Exports PDF/SVG plus reports, metadata, source data, and render-QA evidence

## Structure

- `SKILL.md` - skill entry point and coordinator
- `phases/` - data detection, chart planning, code generation, export
- `specs/` - chart catalog, domain playbooks, journal profiles, workflow policies
- `templates/` - palette presets and panel layout recipes

## License

MIT

</details>

<details id="中文">
<summary><a href="#">English</a> | <b>中文</b></summary>

# SciFig Generate 技能

一个可复用的 Agent 技能，用于把 CSV、Excel 或矩阵类实验数据转换为投稿级科研图，内置期刊风格默认值、统计约束、渲染质检和可复现导出方案。

## 安装

```bash
git clone https://github.com/Techd81/SciFig.git
cp -r SciFig/.claude/skills/scifig-generate ~/.claude/skills/
```

## 功能

- 先验证真实数据路径，再读取文件
- 识别 tidy、wide、matrix 数据结构和科研领域线索
- 推荐 13 个领域内的 115 种已实现投稿级图表
- 生成 Nature/Cell/Science/Lancet/NEJM/JAMA 风格代码
- 应用自适应视觉密度、配色、图例、布局和性能策略
- 可选调用只读 Agent 做 schema、图表/统计、布局、配色、代码和渲染质检
- 导出 PDF/SVG、报告、元数据、源数据和渲染 QA 证据

## 结构

- `SKILL.md` - 技能入口和协调器
- `phases/` - 数据检测、图表规划、代码生成、导出
- `specs/` - 图表目录、领域手册、期刊配置、工作流策略
- `templates/` - 调色板预设和多 panel 布局模板

## 许可证

MIT

</details>
