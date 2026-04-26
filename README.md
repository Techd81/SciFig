<details open>
<summary><b>English</b> | <a href="#中文">中文</a></summary>

# SciFig Generate Skill

A reusable agent skill that transforms experimental data (CSV, Excel, or matrix tables) into publication-ready scientific figures with journal-style defaults, statistical guardrails, and reproducible export plans.

## Install

```bash
git clone https://github.com/Techd81/SciFig.git
cp -r SciFig/.claude/skills/scifig-generate ~/.claude/skills/
```

## What It Does

- Upload CSV/Excel/matrix data
- Auto-detect data structure (tidy vs matrix) and scientific domain
- Recommend publication-grade chart types (35+ charts across 13 domains)
- Generate Nature/Cell/Science/Lancet/NEJM/JAMA-aligned figure code
- Apply colorblind-safe palettes and multi-panel composition
- Export vector graphics (PDF/SVG) with statistical reports

## Structure

- `SKILL.md` — Skill entry point and orchestrator
- `phases/` — Execution phases (data detect, chart recommend, code gen, export)
- `specs/` — Chart catalog, domain playbooks, journal profiles
- `templates/` — Palette presets, panel layout recipes

## License

MIT

</details>

<details id="中文">
<summary><a href="#">English</a> | <b>中文</b></summary>

# SciFig Generate 技能

一个可复用的 Agent 技能，用于把实验数据（CSV、Excel 或矩阵类表格）转换为投稿级科研图工作流，提供期刊风格默认值、统计约束和可复现的导出方案。

## 安装

```bash
git clone https://github.com/Techd81/SciFig.git
cp -r SciFig/.claude/skills/scifig-generate ~/.claude/skills/
```

## 功能

- 上传 CSV/Excel/矩阵数据
- 自动识别数据结构（tidy vs matrix）和科研领域
- 推荐投稿级图表类型（35+ 种图表，13 个领域）
- 生成 Nature/Cell/Science/Lancet/NEJM/JAMA 风格代码
- 应用色盲安全配色和多 panel 组图
- 导出矢量图形（PDF/SVG）和统计报告

## 结构

- `SKILL.md` — 技能入口和协调器
- `phases/` — 执行阶段（数据检测、图表推荐、代码生成、导出）
- `specs/` — 图表目录、领域手册、期刊配置
- `templates/` — 调色板预设、布局模板

## 许可证

MIT

</details>
