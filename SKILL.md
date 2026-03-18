# skill-health-keeper

技能健康度管家 - 检查技能是否符合 skill-forge 规范

## 元信息

- **版本**: v1.0.0
- **作者**: spark
- **创建时间**: 2026-03-10
- **触发词**: health, 健康度，检查技能

## 核心功能

- 检查技能是否符合 skill-forge 规范
- 给出🟢🟡🔴评价
- 生成 JSON 结果和 MD 报告

## P0 检查项

1. **SKILL.md 行数 ≤ 250** - 使用 `wc -l` 检查
2. **必需文件存在** - SKILL.md + CHANGELOG.md 必须存在
3. **YAML 格式有效** - 使用 `python yaml.load` 验证
4. **技能命名 kebab-case** - 使用正则验证
5. **版本号 semver 格式** - vX.Y.Z 格式验证

## P1 检查项

1. **引用文件存在** - 技能/command 中提到的脚本/文档实际存在
2. **孤儿文件** - 检测有脚本未被技能提及
3. **生成 MD 报告** - agent 编排生成可读报告

## 灯号逻辑

- 🟢 **绿灯**: 全部通过
- 🟡 **黄灯**: 1-2 个🟡问题
- 🔴 **红灯**: 1 个🔴问题 或 3+🟡问题

## 检查规范

> **注**: 规范修改需用户确认

### P0 检查项（阻塞性问题）

| 编号 | 检查项 | 标准 | 检查方式 | 灯号 |
|------|--------|------|----------|------|
| P0-1 | SKILL.md 行数 | ≤ 250 行 | 脚本检测 (`wc -l`) | 🟡 |
| P0-2 | 必需文件存在 | SKILL.md + CHANGELOG.md 必须存在 | 脚本检测 (文件存在性) | 🔴 |
| P0-3 | YAML 格式有效 | 所有 YAML 文件可被解析 | 脚本检测 (`python yaml.load`) | 🔴 |
| P0-4 | 技能命名 kebab-case | 符合 `^[a-z][a-z0-9]*(-[a-z0-9]+)*$` | 脚本检测 (正则匹配) | 🔴 |
| P0-5 | 版本号 semver 格式 | CHANGELOG.md 中包含 vX.Y.Z 格式 | 脚本检测 (正则匹配) | 🟡 |

### P1 检查项（建议性问题）

| 编号 | 检查项 | 标准 | 检查方式 | 灯号 |
|------|--------|------|----------|------|
| P1-1 | 引用文件存在 | SKILL.md 中引用的脚本/文档实际存在 | 脚本检测 (路径解析 + 文件存在性) | 🔴 |
| P1-2 | 孤儿文件 | 所有 scripts/ 中的文件都在 SKILL.md 中被提及 | 脚本检测 (内容搜索) | 🟡 |
| P1-3 | ROADMAP.md 文件存在性 | 技能目录下应有 roadmap.md 或 ROADMAP.md | 脚本检测 (`test -f`) | 🟡 |

### 灯号计算规则

- 🟢 **绿灯**: 无问题
- 🟡 **黄灯**: 1-2 个警告（无错误）
- 🔴 **红灯**: ≥1 个错误 或 ≥3 个警告

**规范修改流程**:
1. 提出修改建议（新增/删除/调整检查项）
2. 用户确认修改
3. 更新本文档和 `scripts/health-check.py`
4. 更新 CHANGELOG.md

## 使用方式

```bash
# 检查单个技能
./scripts/health-check.py skills/skill-name

# 检查所有技能
./scripts/health-check.py skills/

# 查看 JSON 结果
cat resources/skill-health/results.json

# 查看最新报告
ls -lt resources/skill-health/reports/
```

## 输出格式

### JSON Schema

```json
{
  "skill-name": {
    "status": "green|yellow|red",
    "last_check": "2026-03-10T23:00:00Z",
    "issues": [{"type": "warning|error", "message": "..."}]
  }
}
```

### MD 报告格式

```markdown
# 技能健康度报告

**检查时间**: 2026-03-10 23:00
**Agent**: main
**模型**: qwen3.5-plus

## 总览
- 🟢 通过：X 个
- 🟡 警告：Y 个
- 🔴 问题：Z 个

## 详情

### skill-name-1 🟢
全部通过

### skill-name-2 🟡
- SKILL.md 行数：280（超标 30 行）

### skill-name-3 🔴
- 缺少必需文件：CHANGELOG.md
- 引用文件不存在：scripts/missing.sh
```

## 相关文件

- `scripts/health-check.py` - 主检查脚本
- `scripts/json-db.py` - JSON 读写工具
- `commands/check-skill-health.md` - 调用命令
- `resources/skill-health/results.json` - 检查结果
- `resources/skill-health/reports/` - 历史报告

## 变更日志

见 [CHANGELOG.md](CHANGELOG.md)
