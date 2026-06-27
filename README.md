# EPUB Summarizer

A chapter-by-chapter EPUB summarizer using a local Hugging Face model. No API keys required.

## Requirements

- Python 3.9+
- ~2 GB disk space for the default model

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py book.epub
```

This produces `book_summary.txt` with a chapter-by-chapter summary.

### Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output file path |
| `-m, --model` | Hugging Face model name (default: `facebook/bart-large-cnn`) |
| `--device` | Override device: `cpu`, `cuda`, or `mps` |
| `--max-chapters` | Only summarize the first N chapters |

### Examples

```bash
# Use a smaller model
python main.py book.epub --model distilbart-cnn-12-6

# Custom output file
python main.py book.epub -o summary.txt

# Test with first 2 chapters
python main.py book.epub --max-chapters 2

# Force CPU
python main.py book.epub --device cpu
```

## How it works

1. **Parse** — extracts table of contents, chapter titles, and text from the EPUB
2. **Chunk** — splits chapters longer than 1024 tokens at sentence boundaries
3. **Summarize** — runs each chunk through a sequence-to-sequence transformer model
4. **Output** — writes a formatted `.txt` file with per-chapter summaries

## Model notes

The default model (`facebook/bart-large-cnn`) is English-only and optimized for news-style summarization. For different content, try:
- `distilbart-cnn-12-6` — faster, smaller, slightly lower quality
- `google/pegasus-xsum` — better for abstractive/extreme summarization
- `philschmid/bart-large-cnn-samsum` — better for conversational text
