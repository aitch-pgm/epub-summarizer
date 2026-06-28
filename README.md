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
| `-m, --model` | Model for basic summaries (default: `andreaparker/long-summ`) |
| `--detailed` | Also generate a structured summary (Key Ideas, Golden Nuggets, etc.) |
| `--detailed-model` | Model for detailed summaries (default: `microsoft/Phi-3-mini-4k-instruct`) |
| `--device` | Override device: `cpu`, `cuda`, or `mps` |
| `--max-chapters` | Only summarize the first N chapters |

You can override either with `--model` or `--detailed-model`.

### Examples

```bash
# Basic summary
python main.py book.epub

# Basic + detailed structured summary
python main.py book.epub --detailed

# Override both models
python main.py book.epub --detailed \
    --model andreaparker/long-summ \
    --detailed-model microsoft/Phi-3-mini-4k-instruct

# Test with first 2 chapters
python main.py book.epub --max-chapters 2

# Force CPU
python main.py book.epub --device cpu
```

## How it works

1. **Parse** — extracts table of contents, chapter titles, and text from the EPUB
2. **Chunk** — splits chapters longer than the model's context window at sentence boundaries
3. **Summarize** — runs each chunk through the model
4. **Output** — writes one or two `.txt` files:
   - `_summary.txt` — concise per-chapter summaries (encoder-decoder model like LongT5/LED)
   - `_detailed.txt` — structured summaries with Key Ideas, Golden Nuggets, etc. (instruction-tuned model like Phi-3)

## Recommended models

### For basic chapter summaries (`--model` / `_summary.txt`)

| Model | Context | Params | Notes |
|---|---|---|---|
| `andreaparker/long-summ` | 16K | 400M | LED fine-tuned on BookSum. Default. |
| `pszemraj/long-t5-tglobal-base-16384-book-summary` | 16K | 600M | LongT5 fine-tuned on BookSum. Best quality. |
| `pszemraj/pegasus-x-large-book-summary` | 16K | 600M | Pegasus fine-tuned on BookSum. Strong abstractive summaries. |

### For structured detailed summaries (`--detailed-model` / `_detailed.txt`)

| Model | Context | Params | Notes |
|---|---|---|---|
| `microsoft/Phi-3-mini-4k-instruct` | 4K | 3.8B | Excellent instruction following, fast on Apple Silicon. Default. |
| `Qwen/Qwen2.5-7B-Instruct` | 32K | 7B | Handles very long chapters, best structured output. |
| `meta-llama/Llama-3.2-3B-Instruct` | 8K | 3B | Good balance of size and quality. |
