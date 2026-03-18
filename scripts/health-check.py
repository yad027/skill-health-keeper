#!/usr/bin/env python3
"""
技能健康度检查脚本
检查技能是否符合 skill-forge 规范
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# 配置
# 脚本位置: skills/skill-health-keeper/scripts/health-check.py
# 需要回到 workspace 目录
SCRIPT_DIR = Path(__file__).parent  # skills/skill-health-keeper/scripts
SKILL_DIR = SCRIPT_DIR.parent  # skills/skill-health-keeper
WORKSPACE_DIR = SKILL_DIR.parent.parent  # workspace root
SKILLS_DIR = WORKSPACE_DIR / "skills"
RESOURCES_DIR = WORKSPACE_DIR / "resources" / "skill-health"
RESULTS_FILE = RESOURCES_DIR / "results.json"
REPORTS_DIR = RESOURCES_DIR / "reports"

# 确保目录存在
RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def check_skill_md_lines(skill_path: Path) -> dict:
    """P0-1: 检查 SKILL.md 行数 ≤ 250"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {"type": "error", "message": "SKILL.md 不存在"}
    
    with open(skill_md, 'r', encoding='utf-8') as f:
        lines = len(f.readlines())
    
    if lines > 250:
        return {"type": "warning", "message": f"SKILL.md 行数：{lines}（超标 {lines - 250} 行）"}
    return None


def check_required_files(skill_path: Path) -> list:
    """P0-2: 检查必需文件存在"""
    issues = []
    required = ["SKILL.md", "CHANGELOG.md"]
    
    for file in required:
        if not (skill_path / file).exists():
            issues.append({"type": "error", "message": f"缺少必需文件：{file}"})
    
    return issues


def check_yaml_valid(skill_path: Path) -> dict:
    """P0-3: 检查 YAML 格式有效"""
    if not YAML_AVAILABLE:
        return {"type": "warning", "message": "PyYAML 未安装，跳过 YAML 格式检查"}
    
    # 查找技能目录下的 YAML 文件
    yaml_files = list(skill_path.glob("*.yaml")) + list(skill_path.glob("*.yml"))
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            return {"type": "error", "message": f"YAML 格式错误 ({yaml_file.name}): {str(e)[:100]}"}
    
    return None


def check_kebab_case(skill_name: str) -> dict:
    """P0-4: 检查技能命名 kebab-case"""
    pattern = r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$'
    if not re.match(pattern, skill_name):
        return {"type": "error", "message": f"技能命名不符合 kebab-case: {skill_name}"}
    return None


def check_semver_version(skill_path: Path) -> dict:
    """P0-5: 检查版本号 semver 格式 vX.Y.Z"""
    changelog = skill_path / "CHANGELOG.md"
    if not changelog.exists():
        return None
    
    with open(changelog, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找版本号
    pattern = r'\[v(\d+)\.(\d+)\.(\d+)\]'
    matches = re.findall(pattern, content)
    
    if not matches:
        return {"type": "warning", "message": "CHANGELOG.md 中未找到 semver 版本号 (vX.Y.Z)"}
    
    return None


def check_referenced_files(skill_path: Path) -> list:
    """P1-1: 检查引用文件存在"""
    issues = []
    skill_md = skill_path / "SKILL.md"
    
    if not skill_md.exists():
        return issues
    
    with open(skill_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 只检查非代码块中的引用
    in_code_block = False
    referenced_files = set()
    
    for line in lines:
        # 检测代码块
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # 跳过代码块中的内容
        if in_code_block:
            continue
        
        # 提取引用的文件路径 (相对路径，不包含 URL 或绝对路径)
        # 匹配格式：scripts/xxx, commands/xxx, resources/xxx
        patterns = [
            r'(?<![`/])(scripts/[a-zA-Z0-9._/-]+)(?![`])',
            r'(?<![`/])(commands/[a-zA-Z0-9._/-]+)(?![`])',
            r'(?<![`/])(resources/[a-zA-Z0-9._/-]+)(?![`])'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for ref_file in matches:
                # 清理末尾的标点
                ref_file = ref_file.rstrip('`.,;:)]')
                referenced_files.add(ref_file)
    
    # 验证引用的文件
    for ref_file in referenced_files:
        # 跳过示例中的占位符
        if 'missing' in ref_file.lower() or 'example' in ref_file.lower():
            continue
        
        # 转换为绝对路径
        if ref_file.startswith('scripts/') or ref_file.startswith('commands/'):
            abs_path = skill_path.parent.parent / ref_file
        elif ref_file.startswith('resources/'):
            abs_path = skill_path.parent.parent / ref_file
        else:
            continue
        
        if not abs_path.exists():
            issues.append({"type": "error", "message": f"引用文件不存在：{ref_file}"})
    
    return issues


def check_orphan_files(skill_path: Path) -> list:
    """P1-2: 检查孤儿文件（脚本未被技能提及）"""
    issues = []
    skill_md = skill_path / "SKILL.md"
    scripts_dir = skill_path / "scripts"
    
    if not skill_md.exists() or not scripts_dir.exists():
        return issues
    
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取所有脚本文件
    script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
    
    for script in script_files:
        script_name = script.name
        # 检查脚本是否在 SKILL.md 中被提及
        if script_name not in content and script.stem not in content:
            issues.append({"type": "warning", "message": f"孤儿文件：scripts/{script_name} 未被技能提及"})
    
    return issues


def check_roadmap_exists(skill_path: Path) -> dict:
    """P1-3: 检查 ROADMAP.md 文件存在性"""
    roadmap_lower = skill_path / "roadmap.md"
    roadmap_upper = skill_path / "ROADMAP.md"
    
    if not roadmap_lower.exists() and not roadmap_upper.exists():
        return {"type": "warning", "message": "缺少 ROADMAP.md 文件"}
    return None


def check_skill(skill_path: Path) -> dict:
    """检查单个技能"""
    skill_name = skill_path.name
    issues = []
    
    # P0 检查
    # 1. SKILL.md 行数
    issue = check_skill_md_lines(skill_path)
    if issue:
        issues.append(issue)
    
    # 2. 必需文件
    issues.extend(check_required_files(skill_path))
    
    # 3. YAML 格式
    issue = check_yaml_valid(skill_path)
    if issue:
        issues.append(issue)
    
    # 4. kebab-case 命名
    issue = check_kebab_case(skill_name)
    if issue:
        issues.append(issue)
    
    # 5. semver 版本号
    issue = check_semver_version(skill_path)
    if issue:
        issues.append(issue)
    
    # P1 检查
    # 1. 引用文件存在
    issues.extend(check_referenced_files(skill_path))
    
    # 2. 孤儿文件
    issues.extend(check_orphan_files(skill_path))
    
    # 3. ROADMAP.md 存在性
    issue = check_roadmap_exists(skill_path)
    if issue:
        issues.append(issue)
    
    # 计算状态
    errors = [i for i in issues if i["type"] == "error"]
    warnings = [i for i in issues if i["type"] == "warning"]
    
    if len(errors) > 0 or len(warnings) >= 3:
        status = "red"
    elif len(warnings) >= 1:
        status = "yellow"
    else:
        status = "green"
    
    return {
        "status": status,
        "last_check": datetime.now().isoformat(),
        "issues": issues
    }


def load_results() -> dict:
    """加载现有结果"""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_results(results: dict):
    """保存结果"""
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def generate_report(results: dict, skills_to_include: list = None) -> list:
    """为指定技能生成独立的 MD 报告
    
    Args:
        results: 所有技能的结果字典
        skills_to_include: 要生成报告的技能名列表（None 表示所有）
    """
    now = datetime.now()
    agent = os.environ.get("AGENT", "main")
    model = os.environ.get("MODEL", "qwen3.5-plus")
    timestamp = now.strftime('%Y-%m-%d-%H%M%S')
    
    report_files = []
    
    # 只处理指定的技能
    skills_to_process = skills_to_include if skills_to_include else list(results.keys())
    
    for skill_name in sorted(skills_to_process):
        if skill_name not in results:
            continue
            
        result = results[skill_name]
        # 统计单个技能的问题
        errors = [i for i in result["issues"] if i["type"] == "error"]
        warnings = [i for i in result["issues"] if i["type"] == "warning"]
        
        emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(result["status"], "⚪")
        
        report = f"""# 技能健康度报告 - {skill_name}

**检查时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}
**Agent**: {agent}
**模型**: {model}
**技能状态**: {result["status"]} {emoji}

## 问题统计
- ❌ 错误：{len(errors)} 个
- ⚠️ 警告：{len(warnings)} 个

## 详细问题

"""
        
        if not result["issues"]:
            report += "✅ 全部通过\n\n"
        else:
            for issue in result["issues"]:
                icon = "❌" if issue["type"] == "error" else "⚠️"
                report += f"- {icon} [{issue['type'].upper()}] {issue['message']}\n"
            report += "\n"
        
        # 保存独立报告
        date_dir = REPORTS_DIR / now.strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"{skill_name}-{timestamp}.md"
        report_file = date_dir / report_filename
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        report_files.append(report_file)
    
    return report_files


def save_report(results: dict, skills_to_include: list = None) -> list:
    """为指定技能生成独立报告
    
    Args:
        results: 所有技能的结果字典
        skills_to_include: 要生成报告的技能名列表（None 表示所有）
    """
    return generate_report(results, skills_to_include)


def main():
    if len(sys.argv) < 2:
        print("用法: python health-check.py <skill-path|skills/>")
        print("示例:")
        print("  python health-check.py skills/skill-name")
        print("  python health-check.py skills/")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    
    # 确定检查范围
    if target.is_dir() and target.name == "skills":
        # 检查所有技能
        skills_to_check = [d for d in target.iterdir() if d.is_dir()]
    else:
        # 检查单个技能
        skills_to_check = [target]
    
    print(f"🔍 开始检查 {len(skills_to_check)} 个技能...")
    
    # 首次运行时自动创建空 results.json
    if not RESULTS_FILE.exists():
        print(f"📝 首次运行，创建空 results.json...")
        save_results({})
    
    # 加载现有结果
    results = load_results()
    
    # 检查每个技能
    for skill_path in skills_to_check:
        if not skill_path.exists():
            print(f"❌ 技能不存在：{skill_path}")
            continue
        
        print(f"检查 {skill_path.name}...", end=" ")
        result = check_skill(skill_path)
        results[skill_path.name] = result
        
        emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(result["status"], "⚪")
        print(f"{emoji} {result['status']} ({len(result['issues'])} 个问题)")
    
    # 保存结果
    save_results(results)
    print(f"\n💾 结果已保存到：{RESULTS_FILE}")
    
    # 为当前检查的技能生成独立报告（而不是所有历史技能）
    current_skill_names = [s.name for s in skills_to_check]
    report_files = save_report(results, current_skill_names)
    print(f"\n📄 报告已保存到:")
    for report_file in report_files:
        print(f"   {report_file}")
    
    # 输出摘要
    green = sum(1 for r in results.values() if r["status"] == "green")
    yellow = sum(1 for r in results.values() if r["status"] == "yellow")
    red = sum(1 for r in results.values() if r["status"] == "red")
    
    print(f"\n📊 总览：🟢{green} 🟡{yellow} 🔴{red}")


if __name__ == "__main__":
    main()
