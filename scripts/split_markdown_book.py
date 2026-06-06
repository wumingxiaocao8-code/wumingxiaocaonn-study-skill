#!/usr/bin/env python3
"""
将全书的单个 Markdown 文件按 ## 标题拆分为章节文件。
运行失败时 Skill 应回退到手动方式。
"""
import re
import sys
from pathlib import Path


def split_book(input_path: str, output_dir: str) -> dict:
    """
    按 # 和 ## 标题拆分 markdown 文件。
    每个 ## 节保存为独立文件，# 标题作为文件夹或前缀。
    """
    input_file = Path(input_path)
    if not input_file.exists():
        return {"error": f"文件不存在: {input_path}"}

    text = input_file.read_text(encoding="utf-8")
    lines = text.split("\n")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    chapter_pattern = re.compile(r"^#\s+(.+)$")
    section_pattern = re.compile(r"^##\s+(.+)$")

    current_chapter = "前言"
    current_section = None
    current_content = []
    files_created = []

    for line in lines:
        ch_match = chapter_pattern.match(line)
        sec_match = section_pattern.match(line)

        if ch_match:
            # 保存上一节的积累
            if current_content and current_section is not None:
                filename = sanitize_filename(f"{current_chapter} - {current_section}.md")
                write_section(output / filename, current_chapter, current_section, current_content)
                files_created.append(filename)

            current_chapter = ch_match.group(1).strip()
            current_section = None
            current_content = [line]
        elif sec_match:
            # 保存上一节
            if current_content and current_section is not None:
                filename = sanitize_filename(f"{current_chapter} - {current_section}.md")
                write_section(output / filename, current_chapter, current_section, current_content)
                files_created.append(filename)

            current_section = sec_match.group(1).strip()
            current_content = [f"# {current_chapter}", "", line]  # 每节文件带章标题
        else:
            current_content.append(line)

    # 保存最后一节
    if current_content and current_section is not None:
        filename = sanitize_filename(f"{current_chapter} - {current_section}.md")
        write_section(output / filename, current_chapter, current_section, current_content)
        files_created.append(filename)
    elif current_content and current_section is None:
        # 没有节的章内容（前言等）
        filename = sanitize_filename(f"{current_chapter}.md")
        write_section(output / filename, current_chapter, "概述", current_content)
        files_created.append(filename)

    return {"output_dir": str(output), "files_created": files_created, "count": len(files_created)}


def sanitize_filename(name: str) -> str:
    """移除文件名中不允许的字符。"""
    # 替换 Windows/Linux 文件名非法字符
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, "-")
    # 限制长度
    if len(name) > 200:
        name = name[:200]
    return name.strip()


def write_section(filepath: Path, chapter: str, section: str, content: list):
    """写入拆分后的章节文件。"""
    header = f"<!-- 章: {chapter} | 节: {section} -->\n\n"
    filepath.write_text(header + "\n".join(content), encoding="utf-8")


def main():
    if len(sys.argv) < 3:
        print("用法: python split_markdown_book.py <book.md> <output_dir>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    result = split_book(input_path, output_dir)

    if "error" in result:
        print(result["error"], file=sys.stderr)
        sys.exit(1)

    print(f"拆分完成，共 {result['count']} 个文件，输出到 {result['output_dir']}")
    for f in result["files_created"]:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
