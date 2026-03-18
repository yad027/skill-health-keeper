# Changelog

All notable changes to skill-health-keeper will be documented in this file.

## [v1.1.0] - 2026-03-10

### Added
- P1-3 检查项：ROADMAP.md 文件存在性检查
- 意图识别交互菜单（skill-forge 自动调用）
- 报告格式改进：增加 Agent 和模型信息

### Changed
- 改进检查逻辑，区分 P0/P1 优先级

## [v1.0.0] - 2026-03-10

### Added
- 初始版本
- P0 检查项：SKILL.md 行数、必需文件、YAML 格式、命名规范、版本号格式
- P1 检查项：引用文件存在性、孤儿文件检测
- 灯号逻辑：🟢🟡🔴三色评价
- JSON 结果输出
- MD 报告生成
- health-check.py 主检查脚本
- json-db.py JSON 读写工具
- check-skill-health.md 调用命令
