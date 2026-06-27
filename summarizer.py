import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from tqdm import tqdm

DEFAULT_MODEL = "facebook/bart-large-cnn"
CHUNK_MAX_TOKENS = 1024
SUMMARY_MAX_LENGTH = 250
SUMMARY_MIN_LENGTH = 30


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

    def summarize_chapters(self, chapters):
        results = []
        for ch in tqdm(chapters, desc="Summarizing"):
            summary = self.summarize_text(ch["text"])
            results.append({"title": ch["title"], "summary": summary})
        return results
