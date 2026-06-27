import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def _get_title(book):
    title = book.get_metadata("DC", "title")
    return title[0][0] if title else "Unknown Title"


def _get_author(book):
    creator = book.get_metadata("DC", "creator")
    return creator[0][0] if creator else "Unknown Author"


def _clean_text(html):
    soup = BeautifulSoup(html, "lxml")
    for elem in soup(["script", "style", "nav"]):
        elem.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_toc_map(toc_entries, result=None):
    if result is None:
        result = {}
    for entry in toc_entries:
        if isinstance(entry, epub.Link):
            href = entry.href.split("#")[0]
            result[href] = entry.title
        elif isinstance(entry, tuple):
            _build_toc_map(entry[1], result)
    return result


def extract_chapters(epub_path):
    book = epub.read_epub(epub_path)
    title = _get_title(book)
    author = _get_author(book)
    toc_map = _build_toc_map(book.toc)

    chapters = []
    seen_names = set()

    for spine_id, _ in book.spine:
        item = book.get_item_with_id(spine_id)
        if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        name = item.get_name()
        if name in seen_names:
            continue
        seen_names.add(name)

        chapter_title = toc_map.get(name) or toc_map.get("/" + name)

        content = item.get_content()
        soup = BeautifulSoup(content, "lxml")

        if not chapter_title:
            if soup.title and soup.title.string:
                chapter_title = soup.title.string.strip()
            else:
                for tag in ["h1", "h2", "h3", "h4"]:
                    heading = soup.find(tag)
                    if heading and heading.get_text(strip=True):
                        chapter_title = heading.get_text(strip=True)
                        break

        if not chapter_title:
            chapter_title = f"Chapter {len(chapters) + 1}"

        text = _clean_text(content)
        if text:
            chapters.append({"title": chapter_title, "text": text})

    return {"title": title, "author": author, "chapters": chapters}
