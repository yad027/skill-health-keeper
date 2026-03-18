#!/usr/bin/env python3
"""
JSON 数据库读写工具
用于技能健康度检查结果的存储和查询
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 配置
# 脚本位置: skills/skill-health-keeper/scripts/json-db.py
SCRIPT_DIR = Path(__file__).parent  # skills/skill-health-keeper/scripts
SKILL_DIR = SCRIPT_DIR.parent  # skills/skill-health-keeper
WORKSPACE_DIR = SKILL_DIR.parent.parent  # workspace root
DEFAULT_DB_PATH = WORKSPACE_DIR / "resources" / "skill-health" / "results.json"


def load_db(db_path: Path = DEFAULT_DB_PATH) -> dict:
    """加载 JSON 数据库"""
    if not db_path.exists():
        return {}
    
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_db(data: dict, db_path: Path = DEFAULT_DB_PATH):
    """保存 JSON 数据库"""
    # 确保目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_skill(skill_name: str, db_path: Path = DEFAULT_DB_PATH) -> dict:
    """获取单个技能的健康度"""
    db = load_db(db_path)
    return db.get(skill_name, {})


def update_skill(skill_name: str, data: dict, db_path: Path = DEFAULT_DB_PATH):
    """更新单个技能的健康度"""
    db = load_db(db_path)
    db[skill_name] = data
    save_db(db, db_path)


def delete_skill(skill_name: str, db_path: Path = DEFAULT_DB_PATH):
    """删除单个技能的健康度记录"""
    db = load_db(db_path)
    if skill_name in db:
        del db[skill_name]
        save_db(db, db_path)


def list_skills(db_path: Path = DEFAULT_DB_PATH) -> list:
    """列出所有技能"""
    db = load_db(db_path)
    return list(db.keys())


def get_summary(db_path: Path = DEFAULT_DB_PATH) -> dict:
    """获取总览统计"""
    db = load_db(db_path)
    
    summary = {
        "total": len(db),
        "green": 0,
        "yellow": 0,
        "red": 0
    }
    
    for skill in db.values():
        status = skill.get("status", "unknown")
        if status in summary:
            summary[status] += 1
    
    return summary


def main():
    if len(sys.argv) < 2:
        print("JSON 数据库工具 - 技能健康度结果管理")
        print()
        print("用法:")
        print("  python json-db.py list                     # 列出所有技能")
        print("  python json-db.py get <skill-name>         # 获取技能健康度")
        print("  python json-db.py summary                  # 获取总览统计")
        print("  python json-db.py update <skill> <json>    # 更新技能数据")
        print("  python json-db.py delete <skill-name>      # 删除技能记录")
        print()
        print("示例:")
        print('  python json-db.py get skill-forge')
        print('  python json-db.py update skill-forge \'{"status":"green","last_check":"2026-03-10T23:00:00Z","issues":[]}\'')
        sys.exit(0)
    
    command = sys.argv[1]
    db_path = DEFAULT_DB_PATH
    
    if command == "list":
        skills = list_skills(db_path)
        if skills:
            print("已记录的技能:")
            for skill in skills:
                print(f"  - {skill}")
        else:
            print("暂无记录")
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("错误：请指定技能名称")
            sys.exit(1)
        skill_name = sys.argv[2]
        result = get_skill(skill_name, db_path)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"未找到技能：{skill_name}")
    
    elif command == "summary":
        summary = get_summary(db_path)
        print(f"总览统计:")
        print(f"  总计：{summary['total']} 个技能")
        print(f"  🟢 通过：{summary['green']} 个")
        print(f"  🟡 警告：{summary['yellow']} 个")
        print(f"  🔴 问题：{summary['red']} 个")
    
    elif command == "update":
        if len(sys.argv) < 4:
            print("错误：请指定技能名称和 JSON 数据")
            sys.exit(1)
        skill_name = sys.argv[2]
        try:
            data = json.loads(sys.argv[3])
            update_skill(skill_name, data, db_path)
            print(f"已更新技能：{skill_name}")
        except json.JSONDecodeError as e:
            print(f"JSON 格式错误：{e}")
            sys.exit(1)
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("错误：请指定技能名称")
            sys.exit(1)
        skill_name = sys.argv[2]
        delete_skill(skill_name, db_path)
        print(f"已删除技能：{skill_name}")
    
    else:
        print(f"未知命令：{command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
