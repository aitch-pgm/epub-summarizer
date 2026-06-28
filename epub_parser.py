import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

SKIP_TITLES = {
    "table of contents", "contents", "copyright", "title page",
    "license", "gutenberg",
}


def _get_title(book):
    title = book.get_metadata("DC", "title")
    return title[0][0] if title else "Unknown Title"


def _get_author(book):
    creator = book.get_metadata("DC", "creator")
    return creator[0][0] if creator else "Unknown Author"


def _file_map(book):
    result = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            result[item.get_name()] = item
    return result


def _collect_toc_entries(toc):
    entries = []
    for entry in toc:
        if isinstance(entry, epub.Link):
            parts = entry.href.split("#", 1)
            if len(parts) == 2:
                skip = any(kw in entry.title.lower() for kw in SKIP_TITLES)
                entries.append(
                    {
                        "title": entry.title.strip(),
                        "file": parts[0],
                        "fragment": parts[1],
                        "skip": skip,
                    }
                )
        elif isinstance(entry, tuple):
            entries.extend(_collect_toc_entries(entry[1]))
    return entries


def _text_for_fragment(soup, frag_id):
    el = soup.find(id=frag_id)
    if el is None:
        return ""
    text = el.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)


def extract_chapters(epub_path):
    book = epub.read_epub(epub_path)
    title = _get_title(book)
    author = _get_author(book)
    files = _file_map(book)
    toc_entries = _collect_toc_entries(book.toc)

    chapters = []
    for entry in toc_entries:
        if entry["skip"]:
            continue
        item = files.get(entry["file"])
        if item is None:
            continue
        soup = BeautifulSoup(item.get_content(), "lxml")
        text = _text_for_fragment(soup, entry["fragment"])
        if text and len(text.split()) >= 100:
            chapters.append({"title": entry["title"], "text": text})

    return {"title": title, "author": author, "chapters": chapters}
