# Curved Surface Reconstruction

[English](#english) | [中文](#中文)

---

## English

### Project Overview
**Curved Surface Reconstruction** converts STL / OBJ / PLY / STEP / point-cloud data into editable CAD surface or solid models.

Unlike faceted mesh files, the reconstructed result is designed for **SolidWorks-native editing**: faces are selectable, topology is manageable, and geometry can be modified with standard CAD operations.

### What Problem It Solves
Mesh and scan data are often locked in triangulated geometry, which limits downstream engineering tasks. This project targets reverse engineering workflows where teams need to:
- transform scan/mesh assets into CAD-editable geometry,
- rebuild smooth and controllable freeform surfaces,
- continue product development in SolidWorks without starting from scratch.

### Key Features
- Multi-source input support: STL, OBJ, PLY, STEP, and point-cloud/scan data.
- Surface-aware reconstruction for curved, organic, and industrial freeform parts.
- CAD-ready output for SolidWorks workflows (selectable/editable faces instead of static facets).
- Suitable for redesign, tolerance updates, feature addition, and manufacturing preparation.
- Structured process for repeatable reverse-modeling tasks.

### Workflow Overview
1. **Import data**: load mesh/CAD/point-cloud input.
2. **Clean & segment**: denoise, align, and isolate meaningful regions.
3. **Fit surfaces**: reconstruct analytic and freeform patches.
4. **Stitch topology**: enforce continuity and watertight boundaries.
5. **Generate CAD body**: build surface body or solid body.
6. **Validate & refine**: compare against source and tune quality level.
7. **Export/use in SolidWorks**: edit faces, add features, and integrate into assemblies.

### Example Cases / Screenshots
> Placeholder: add representative examples here.

- Case A: consumer product shell (organic curves)
- Case B: tooling insert reconstruction
- Case C: scanned ergonomic component

Suggested visuals:
- input mesh / scan,
- intermediate surface patches,
- final SolidWorks-editable model,
- deviation heatmap.

### Quick Start
1. Prepare source data (`.stl`, `.obj`, `.ply`, `.step`, or point-cloud files).
2. Run the reconstruction workflow in your processing environment.
3. Export reconstructed surfaces/solids to your CAD pipeline.
4. Open the result in SolidWorks and verify face-level editability.

> Note: This repository currently focuses on project documentation and workflow definition. Add your implementation scripts/pipeline modules in this repository structure as needed.

### Output Quality Levels
Use quality levels based on downstream use:

- **L1 — Fast Draft**
  - Goal: rapid shape recovery for concept iteration.
  - Characteristics: lighter fitting, faster turnaround.

- **L2 — Engineering**
  - Goal: balanced fidelity and editability for daily design work.
  - Characteristics: stable topology, practical accuracy, good performance.

- **L3 — High Fidelity**
  - Goal: precision-oriented reconstruction for critical surfaces.
  - Characteristics: tighter tolerance, denser control, extended processing.

### Contribution Guide
Contributions are welcome.

- Open an issue describing the problem, use case, or enhancement.
- Submit a pull request with focused, reviewable changes.
- Keep changes reproducible and include before/after evidence where possible.
- For workflow updates, document assumptions, input format, and expected output quality.

### License
This project is released under the **MIT License**. See `LICENSE` for details.

---

## 中文

### 项目简介
**Curved Surface Reconstruction（曲面重建）**面向 STL / OBJ / PLY / STEP / 点云扫描数据，目标是将其转换为可编辑的 CAD 曲面或实体模型。

与三角面片网格不同，重建结果可用于 **SolidWorks 原生编辑**：面可选中、拓扑可管理、几何可继续按 CAD 方式修改。

### 解决的问题
网格与扫描数据通常被锁定在离散三角面结构中，后续工程修改能力有限。本项目聚焦逆向建模场景，帮助团队：
- 将扫描/网格资产转化为 CAD 可编辑几何，
- 重建平滑且可控的自由曲面，
- 在 SolidWorks 中直接继续开发，而不是从零重画。

### 核心特性
- 支持多种输入来源：STL、OBJ、PLY、STEP 与点云/扫描数据。
- 面向曲面特征的重建能力，适合有机外形与工业自由曲面。
- 输出可进入 SolidWorks 流程（面可选可改，而非静态面片）。
- 适用于改型、公差调整、特征补加与制造前准备。
- 提供结构化流程，便于重复执行逆向重建任务。

### 工作流概览
1. **导入数据**：加载网格/CAD/点云输入。
2. **清理与分区**：降噪、对齐并提取有效区域。
3. **曲面拟合**：重建解析面与自由曲面片。
4. **拓扑拼接**：保证连续性与封闭边界。
5. **生成 CAD 体**：构建曲面体或实体体。
6. **校核与优化**：与源数据比对并调整质量级别。
7. **导入 SolidWorks 使用**：继续编辑面、添加特征并装配应用。

### 示例案例 / 截图
> 占位：可在此补充典型案例。

- 案例 A：消费品外壳（有机曲面）
- 案例 B：模具嵌件重建
- 案例 C：人体工学扫描件

建议展示：
- 原始网格/点云输入，
- 中间曲面片结果，
- 最终 SolidWorks 可编辑模型，
- 偏差热力图。

### 快速开始
1. 准备源数据（`.stl`、`.obj`、`.ply`、`.step` 或点云文件）。
2. 在你的处理环境中执行重建流程。
3. 将重建后的曲面/实体导出到 CAD 管线。
4. 在 SolidWorks 中打开并验证面级可编辑性。

> 说明：当前仓库主要提供项目定位与流程文档。可按需要在本仓库中补充实现脚本与处理模块。

### 输出质量等级
可根据下游目标选择质量等级：

- **L1 — 快速草模**
  - 目标：快速恢复外形，用于概念迭代。
  - 特征：拟合更轻量、处理更快。

- **L2 — 工程级**
  - 目标：在精度与可编辑性之间取得平衡，满足日常设计。
  - 特征：拓扑稳定、精度实用、性能均衡。

- **L3 — 高保真**
  - 目标：面向关键曲面的高精度重建。
  - 特征：容差更严格、控制更细、处理时间更长。

### 贡献指南
欢迎贡献。

- 先通过 Issue 描述问题、场景或改进方向。
- 通过 Pull Request 提交聚焦且可审查的改动。
- 尽量保证改动可复现，并附带前后对比证据。
- 若更新流程，请明确输入假设、数据格式与期望输出质量。

### 许可证
本项目采用 **MIT License** 开源协议，详情请见 `LICENSE`。
