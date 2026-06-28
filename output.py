import re
from datetime import datetime

SEPARATOR = "\u2500" * 60


def _strip_section(text, *section_headers):
    for header in section_headers:
        text = re.sub(
            rf"\n*### {re.escape(header)}.*?(?=\n### |\n*$)",
            "",
            text,
            flags=re.DOTALL,
        )
    return text.strip()


def _merge_duplicate_sections(text):
    parts = re.split(r"\n(?=### )", text)
    sections = {}
    order = []
    rest = parts[1:] if len(parts) > 1 else []
    first = parts[0].strip()

    for part in rest:
        lines = part.split("\n")
        header = lines[0].lstrip("### ").strip().rstrip(":")
        content = "\n".join(lines[1:]).strip()
        if header not in sections:
            sections[header] = []
            order.append(header)
        sections[header].append(content)

    result = [first] if first else []
    for name in order:
        result.append(f"### {name}")
        result.append("\n\n".join(sections[name]))
    return "\n\n".join(result)


def write_summary(epub_info, chapter_summaries, model_name, output_path):
    lines = []

    lines.append(f"Book: {epub_info['title']}")
    lines.append(f"Author: {epub_info['author']}")
    lines.append(f"Summarized: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Model: {model_name}")
    lines.append(f"Chapters: {len(chapter_summaries)}")
    lines.append("")

    for i, cs in enumerate(chapter_summaries, 1):
        lines.append(SEPARATOR)
        lines.append(f"Chapter {i}: {cs['title']}")
        lines.append("")
        lines.append(cs["summary"])
        lines.append("")

    lines.append(SEPARATOR)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def write_detailed_summary(epub_info, chapter_summaries, model_name, output_path):
    lines = []

    lines.append(f"Book: {epub_info['title']}")
    lines.append(f"Author: {epub_info['author']}")
    lines.append(f"Summarized: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Model: {model_name}")
    lines.append(f"Chapters: {len(chapter_summaries)}")
    lines.append("")

    for i, cs in enumerate(chapter_summaries, 1):
        lines.append(SEPARATOR)
        lines.append(f"Chapter {i}: {cs['title']}")
        lines.append("")
        summary = cs["summary"]
        summary = _strip_section(summary, "Practical and Applicable", "Practical Wisdom")
        summary = _merge_duplicate_sections(summary)
        lines.append(summary)
        lines.append("")

    lines.append(SEPARATOR)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
