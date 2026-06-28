import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from tqdm import tqdm

DEFAULT_MODEL = "andreaparker/long-summ"
DETAILED_MODEL = "microsoft/Phi-3-mini-4k-instruct"
CHUNK_MAX_TOKENS = 1024
SUMMARY_MAX_LENGTH = 250
SUMMARY_MIN_LENGTH = 30
DETAILED_MAX_LENGTH = 600
DETAILED_MIN_LENGTH = 100

DETAILED_PROMPT = """You are an expert in book summarization. Please summarize the given chapter of the book with the following details:

- **Key Ideas**: Highlight the main points and arguments presented.
- **Golden Nuggets**: Extract the most valuable and insightful quotes or concepts.
- **Practical and Applicable**: Identify the principles or advice that can be immediately applied in real life.
- **Paradigms and Thinking Models**: Outline the paradigms or thinking models introduced or discussed in the chapter.

Ensure the summary is concise, clear, and well-structured. Use bullet points for key ideas and golden nuggets for ease of understanding, and provide actionable steps where applicable. Focus on delivering value that can be applied across different disciplines.

Chapter text:
"""


def _get_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


class Summarizer:
    def __init__(self, model_name=DEFAULT_MODEL, device=None):
        self.device = device or _get_device()
        print(f"Loading model '{model_name}' on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(
            self.device
        )
        self.model_name = model_name

    def _chunk_text(self, text):
        sentences = _split_sentences(text)
        chunks = []
        current = []
        current_tokens = 0

        for sentence in sentences:
            tokens = len(self.tokenizer.encode(sentence))
            if current_tokens + tokens > CHUNK_MAX_TOKENS and current:
                chunks.append(" ".join(current))
                current = []
                current_tokens = 0
            current.append(sentence)
            current_tokens += tokens

        if current:
            chunks.append(" ".join(current))

        return chunks or [text]

    def _summarize_chunk(self, chunk):
        inputs = self.tokenizer(
            chunk,
            max_length=CHUNK_MAX_TOKENS,
            truncation=True,
            return_tensors="pt",
        ).to(self.device)

        summary_ids = self.model.generate(
            inputs.input_ids,
            max_length=SUMMARY_MAX_LENGTH,
            min_length=SUMMARY_MIN_LENGTH,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True,
        )

        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    def summarize_text(self, text):
        if not text.strip():
            return ""
        chunks = self._chunk_text(text)
        summaries = [self._summarize_chunk(c) for c in chunks]
        return " ".join(summaries)

    def summarize_text_structured(self, text):
        if not text.strip():
            return ""
        sentences = _split_sentences(text)
        chunks = []
        current = []
        current_tokens = 0
        prompt_tokens = len(self.tokenizer.encode(DETAILED_PROMPT))
        effective_max = CHUNK_MAX_TOKENS - prompt_tokens

        for sentence in sentences:
            tokens = len(self.tokenizer.encode(sentence))
            if current_tokens + tokens > effective_max and current:
                chunks.append(DETAILED_PROMPT + " ".join(current))
                current = []
                current_tokens = 0
            current.append(sentence)
            current_tokens += tokens

        if current:
            chunks.append(DETAILED_PROMPT + " ".join(current))

        if not chunks:
            chunks = [DETAILED_PROMPT + text]

        summaries = []
        for chunk in chunks:
            inputs = self.tokenizer(
                chunk,
                max_length=CHUNK_MAX_TOKENS,
                truncation=True,
                return_tensors="pt",
            ).to(self.device)
            summary_ids = self.model.generate(
                inputs.input_ids,
                max_length=DETAILED_MAX_LENGTH,
                min_length=DETAILED_MIN_LENGTH,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True,
            )
            summaries.append(
                self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            )
        return "\n\n".join(summaries)

    def summarize_chapters(self, chapters):
        results = []
        for ch in tqdm(chapters, desc="Summarizing"):
            summary = self.summarize_text(ch["text"])
            results.append({"title": ch["title"], "summary": summary})
        return results

    def summarize_chapters_structured(self, chapters):
        results = []
        for ch in tqdm(chapters, desc="Summarizing (detailed)"):
            summary = self.summarize_text_structured(ch["text"])
            results.append({"title": ch["title"], "summary": summary})
        return results
