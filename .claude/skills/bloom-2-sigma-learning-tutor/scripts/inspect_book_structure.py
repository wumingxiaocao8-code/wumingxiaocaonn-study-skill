#!/usr/bin/env python3
"""
扫描 Markdown 书籍文件，提取章节结构并输出 JSON。
用作模块拆分的辅助工具。运行失败时 Skill 应回退到手动方式。
"""
import re
import sys
import json
from pathlib import Path


def inspect_book(filepath: str) -> dict:
    """分析书籍的章节结构、字数分布。"""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"文件不存在: {filepath}"}

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    chapters = []
    current_chapter = None
    current_section = None
    total_chars = 0
    chapter_pattern = re.compile(r"^#\s+(.+)$")
    section_pattern = re.compile(r"^##\s+(.+)$")
    subsection_pattern = re.compile(r"^###\s+(.+)$")

    for line in lines:
        ch_match = chapter_pattern.match(line)
        sec_match = section_pattern.match(line)
        sub_match = subsection_pattern.match(line)

        if ch_match:
            if current_chapter:
                current_chapter["char_count"] = current_chapter["char_count"]
                chapters.append(current_chapter)
            current_chapter = {
                "title": ch_match.group(1).strip(),
                "level": 1,
                "char_count": 0,
                "sections": [],
            }
            current_section = None
        elif sec_match and current_chapter:
            if current_section:
                current_chapter["sections"].append(current_section)
            current_section = {
                "title": sec_match.group(1).strip(),
                "level": 2,
                "char_count": 0,
                "subsections": [],
            }
        elif sub_match and current_section:
            current_section["subsections"].append(
                {"title": sub_match.group(1).strip(), "level": 3, "char_count": 0}
            )
        else:
            char_count = len(line)
            total_chars += char_count
            if current_section:
                current_section["char_count"] += char_count
            elif current_chapter:
                current_chapter["char_count"] += char_count

    # 处理最后一章
    if current_section:
        current_chapter["sections"].append(current_section)
    if current_chapter:
        current_chapter["char_count"] = current_chapter["char_count"]
        chapters.append(current_chapter)

    # 计算总字数（中文按字符数，英文按空格分词）
    total_words_estimate = total_chars

    result = {
        "file": filepath,
        "total_chars": total_chars,
        "total_words_estimate": total_words_estimate,
        "chapter_count": len(chapters),
        "chapters": chapters,
    }
    return result


def suggest_modules(inspection: dict) -> list:
    """基于字数阈值给出模块拆分建议。"""
    SHORT_THRESHOLD = 3000   # 短章合并阈值（字数）
    LONG_THRESHOLD = 8000    # 长章考虑拆分
    VERY_LONG_THRESHOLD = 12000  # 超长章必须拆分

    chapters = inspection.get("chapters", [])
    if not chapters:
        return []

    modules = []
    module_id = 1
    buffer_chapters = []
    buffer_chars = 0

    for i, ch in enumerate(chapters):
        ch_chars = ch.get("char_count", 0)

        # 如果是短章，尝试和前后的短章缓冲合并
        if ch_chars < SHORT_THRESHOLD:
            buffer_chapters.append(ch)
            buffer_chars += ch_chars
            # 如果缓冲够了或者这是最后一章
            if buffer_chars >= SHORT_THRESHOLD or i == len(chapters) - 1:
                titles = [c["title"] for c in buffer_chapters]
                modules.append({
                    "module_id": module_id,
                    "title": " + ".join(titles),
                    "source": [c["title"] for c in buffer_chapters],
                    "char_count": buffer_chars,
                    "reason": "短章合并" if len(buffer_chapters) > 1 else "标准",
                })
                module_id += 1
                buffer_chapters = []
                buffer_chars = 0
        else:
            # 先处理缓冲区
            if buffer_chapters:
                titles = [c["title"] for c in buffer_chapters]
                modules.append({
                    "module_id": module_id,
                    "title": " + ".join(titles),
                    "source": [c["title"] for c in buffer_chapters],
                    "char_count": buffer_chars,
                    "reason": "短章合并",
                })
                module_id += 1
                buffer_chapters = []
                buffer_chars = 0

            # 处理当前章
            if ch_chars > VERY_LONG_THRESHOLD and ch.get("sections"):
                # 超长章按节拆分
                sections = ch["sections"]
                sec_buffer = []
                sec_chars = 0
                for j, sec in enumerate(sections):
                    sec_c = sec.get("char_count", 0)
                    sec_buffer.append(sec)
                    sec_chars += sec_c
                    if sec_chars >= 4000 or j == len(sections) - 1:
                        modules.append({
                            "module_id": module_id,
                            "title": f"{ch['title']} — {' + '.join(s['title'] for s in sec_buffer)}",
                            "source": [ch["title"]] + [s["title"] for s in sec_buffer],
                            "char_count": sec_chars,
                            "reason": "超长章拆分",
                        })
                        module_id += 1
                        sec_buffer = []
                        sec_chars = 0
            elif ch_chars > LONG_THRESHOLD and ch.get("sections"):
                modules.append({
                    "module_id": module_id,
                    "title": ch["title"],
                    "source": [ch["title"]],
                    "char_count": ch_chars,
                    "reason": "长章（建议考虑拆分，已按节结构保留）",
                    "sections": [
                        {"title": s["title"], "char_count": s["char_count"]}
                        for s in ch["sections"]
                    ],
                })
                module_id += 1
            else:
                modules.append({
                    "module_id": module_id,
                    "title": ch["title"],
                    "source": [ch["title"]],
                    "char_count": ch_chars,
                    "reason": "标准",
                })
                module_id += 1

    return modules


def main():
    if len(sys.argv) < 2:
        print("用法: python inspect_book_structure.py <book.md>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    inspection = inspect_book(filepath)

    if "error" in inspection:
        print(inspection["error"], file=sys.stderr)
        sys.exit(1)

    modules = suggest_modules(inspection)
    inspection["suggested_modules"] = modules

    print(json.dumps(inspection, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
