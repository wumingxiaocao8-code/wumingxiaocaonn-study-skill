#!/usr/bin/env python3
"""
扫描 Markdown 书籍文件，提取章节结构并输出 JSON。
用作模块拆分的辅助工具。运行失败时 Skill 应回退到手动方式。
"""
import json
import re
import sys
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
    current_subsection = None
    total_chars = 0

    chapter_pattern = re.compile(r"^#\s+(.+)$")
    section_pattern = re.compile(r"^##\s+(.+)$")
    subsection_pattern = re.compile(r"^###\s+(.+)$")

    def finish_subsection():
        nonlocal current_subsection
        if current_subsection and current_section:
            current_section["subsections"].append(current_subsection)
        current_subsection = None

    def finish_section():
        nonlocal current_section
        finish_subsection()
        if current_section and current_chapter:
            current_chapter["sections"].append(current_section)
        current_section = None

    def finish_chapter():
        nonlocal current_chapter
        finish_section()
        if current_chapter:
            chapters.append(current_chapter)
        current_chapter = None

    for line in lines:
        ch_match = chapter_pattern.match(line)
        sec_match = section_pattern.match(line)
        sub_match = subsection_pattern.match(line)

        if ch_match:
            finish_chapter()
            current_chapter = {
                "title": ch_match.group(1).strip(),
                "level": 1,
                "char_count": 0,
                "sections": [],
            }
        elif sec_match and current_chapter:
            finish_section()
            current_section = {
                "title": sec_match.group(1).strip(),
                "level": 2,
                "char_count": 0,
                "subsections": [],
            }
        elif sub_match and current_section:
            finish_subsection()
            current_subsection = {
                "title": sub_match.group(1).strip(),
                "level": 3,
                "char_count": 0,
            }
        else:
            char_count = len(line)
            total_chars += char_count
            if current_chapter:
                current_chapter["char_count"] += char_count
            if current_section:
                current_section["char_count"] += char_count
            if current_subsection:
                current_subsection["char_count"] += char_count

    finish_chapter()

    return {
        "file": filepath,
        "total_chars": total_chars,
        "total_words_estimate": total_chars,
        "chapter_count": len(chapters),
        "chapters": chapters,
    }


def suggest_modules(inspection: dict) -> list:
    """基于字数阈值给出模块拆分建议。"""
    short_threshold = 3000
    long_threshold = 8000
    very_long_threshold = 12000

    chapters = inspection.get("chapters", [])
    if not chapters:
        return []

    modules = []
    module_id = 1
    buffer_chapters = []
    buffer_chars = 0

    def flush_buffer(reason: str):
        nonlocal module_id, buffer_chapters, buffer_chars
        if not buffer_chapters:
            return
        modules.append(
            {
                "module_id": module_id,
                "title": " + ".join(chapter["title"] for chapter in buffer_chapters),
                "source": [chapter["title"] for chapter in buffer_chapters],
                "char_count": buffer_chars,
                "reason": reason,
            }
        )
        module_id += 1
        buffer_chapters = []
        buffer_chars = 0

    for index, chapter in enumerate(chapters):
        chapter_chars = chapter.get("char_count", 0)

        if chapter_chars < short_threshold:
            buffer_chapters.append(chapter)
            buffer_chars += chapter_chars
            if buffer_chars >= short_threshold or index == len(chapters) - 1:
                reason = "短章合并" if len(buffer_chapters) > 1 else "标准"
                flush_buffer(reason)
            continue

        flush_buffer("短章合并")

        if chapter_chars > very_long_threshold and chapter.get("sections"):
            section_buffer = []
            section_chars = 0
            for section_index, section in enumerate(chapter["sections"]):
                section_buffer.append(section)
                section_chars += section.get("char_count", 0)
                if section_chars >= 4000 or section_index == len(chapter["sections"]) - 1:
                    modules.append(
                        {
                            "module_id": module_id,
                            "title": f"{chapter['title']} — {' + '.join(section['title'] for section in section_buffer)}",
                            "source": [chapter["title"]]
                            + [section["title"] for section in section_buffer],
                            "char_count": section_chars,
                            "reason": "超长章拆分",
                        }
                    )
                    module_id += 1
                    section_buffer = []
                    section_chars = 0
        elif chapter_chars > long_threshold and chapter.get("sections"):
            modules.append(
                {
                    "module_id": module_id,
                    "title": chapter["title"],
                    "source": [chapter["title"]],
                    "char_count": chapter_chars,
                    "reason": "长章（建议考虑拆分，已按节结构保留）",
                    "sections": [
                        {"title": section["title"], "char_count": section["char_count"]}
                        for section in chapter["sections"]
                    ],
                }
            )
            module_id += 1
        else:
            modules.append(
                {
                    "module_id": module_id,
                    "title": chapter["title"],
                    "source": [chapter["title"]],
                    "char_count": chapter_chars,
                    "reason": "标准",
                }
            )
            module_id += 1

    return modules


def print_json(data: dict):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    encoding = sys.stdout.encoding or "utf-8"
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        text = json.dumps(data, ensure_ascii=True, indent=2)
    print(text)


def main():
    if len(sys.argv) < 2:
        print("用法: python inspect_book_structure.py <book.md>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    inspection = inspect_book(filepath)

    if "error" in inspection:
        print(inspection["error"], file=sys.stderr)
        sys.exit(1)

    inspection["suggested_modules"] = suggest_modules(inspection)
    print_json(inspection)


if __name__ == "__main__":
    main()
