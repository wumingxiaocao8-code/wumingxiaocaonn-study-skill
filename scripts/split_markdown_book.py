#!/usr/bin/env python3
"""
将全书的单个 Markdown 文件按 # 和 ## 标题拆分为章节文件。
运行失败时 Skill 应回退到手动方式。
"""
import re
import sys
from pathlib import Path


def split_book(input_path: str, output_dir: str) -> dict:
    """
    按 # 和 ## 标题拆分 markdown 文件。
    每个 ## 节保存为独立文件；无 ## 的章节保存为独立章节文件。
    """
    input_file = Path(input_path)
    if not input_file.exists():
        return {"error": f"文件不存在: {input_path}"}

    output, error = resolve_output_dir(output_dir)
    if error:
        return {"error": error}

    text = input_file.read_text(encoding="utf-8")
    lines = text.split("\n")

    output.mkdir(parents=True, exist_ok=True)

    chapter_pattern = re.compile(r"^#\s+(.+)$")
    section_pattern = re.compile(r"^##\s+(.+)$")

    current_chapter = None
    current_section = None
    current_content = []
    files_created = []

    def has_meaningful_body(content: list[str]) -> bool:
        for item in content:
            stripped = item.strip()
            if stripped and not chapter_pattern.match(item) and not section_pattern.match(item):
                return True
        return False

    def save_current_content(as_overview: bool = False):
        nonlocal current_content
        if not current_content:
            return

        if current_chapter is None:
            chapter = "前言"
            section = "概述"
            filename = sanitize_filename(f"{chapter}.md")
        elif current_section is None:
            chapter = current_chapter
            section = "概述"
            if as_overview:
                if not has_meaningful_body(current_content):
                    current_content = []
                    return
                filename = sanitize_filename(f"{chapter} - {section}.md")
            else:
                filename = sanitize_filename(f"{chapter}.md")
        else:
            chapter = current_chapter
            section = current_section
            filename = sanitize_filename(f"{chapter} - {section}.md")

        write_section(output / filename, chapter, section, current_content)
        files_created.append(filename)
        current_content = []

    for line in lines:
        ch_match = chapter_pattern.match(line)
        sec_match = section_pattern.match(line)

        if ch_match:
            save_current_content(as_overview=False)
            current_chapter = ch_match.group(1).strip()
            current_section = None
            current_content = [line]
        elif sec_match and current_chapter is not None:
            save_current_content(as_overview=True)
            current_section = sec_match.group(1).strip()
            current_content = [f"# {current_chapter}", "", line]
        else:
            current_content.append(line)

    save_current_content(as_overview=False)

    return {"output_dir": str(output), "files_created": files_created, "count": len(files_created)}


def resolve_output_dir(output_dir: str) -> tuple[Path | None, str | None]:
    """Return an absolute output path if it stays under the current workspace."""
    workspace_root = Path.cwd().resolve()
    output = Path(output_dir).resolve()
    try:
        output.relative_to(workspace_root)
    except ValueError:
        return None, f"输出目录在当前工作区之外/outside current workspace: {output}"
    return output, None


def sanitize_filename(name: str) -> str:
    """移除文件名中不允许的字符。"""
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, "-")
    if len(name) > 200:
        name = name[:200]
    return name.strip()


def write_section(filepath: Path, chapter: str, section: str, content: list[str]):
    """写入拆分后的章节文件。"""
    header = f"<!-- 章: {chapter} | 节: {section} -->\n\n"
    filepath.write_text(header + "\n".join(content), encoding="utf-8")


def safe_print(text: str):
    encoding = sys.stdout.encoding or "utf-8"
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        text = text.encode("unicode_escape").decode("ascii")
    print(text)


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

    safe_print(f"拆分完成，共 {result['count']} 个文件，输出到 {result['output_dir']}")
    for filename in result["files_created"]:
        safe_print(f"  - {filename}")


if __name__ == "__main__":
    main()
