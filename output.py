from datetime import datetime

SEPARATOR = "\u2500" * 60


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
        lines.append(cs["summary"])
        lines.append("")

    lines.append(SEPARATOR)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
