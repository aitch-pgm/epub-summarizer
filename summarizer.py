import re
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
)
from tqdm import tqdm

DEFAULT_MODEL = "pszemraj/led-large-book-summary"
DETAILED_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
CHUNK_MAX_TOKENS = 1024
SUMMARY_MAX_LENGTH = 250
SUMMARY_MIN_LENGTH = 30
DETAILED_MAX_LENGTH = 600
DETAILED_CONTEXT_LENGTH = 4096
DETAILED_OUTPUT_RESERVE = 800


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
            num_beams=1,
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


DETAILED_SYSTEM_PROMPT = """You are an expert in book summarization. Please summarize the given chapter of the book with the following details:

- **Key Ideas**: Highlight the main points and arguments presented.
- **Golden Nuggets**: Extract the most valuable and insightful quotes or concepts.
- **Paradigms and Thinking Models**: Outline the paradigms or thinking models introduced or discussed in the chapter.

Ensure the summary is concise, clear, and well-structured. Use bullet points for key ideas and golden nuggets for ease of understanding, and provide actionable steps where applicable. Focus on delivering value that can be applied across different disciplines."""


class InstructSummarizer:
    def __init__(self, model_name=DETAILED_MODEL, device=None):
        self.device = device or _get_device()
        print(f"Loading model '{model_name}' on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(
            self.device
        )
        self.model.generation_config.do_sample = False
        self.model_name = model_name
        self.context_length = min(
            getattr(self.model.config, "max_position_embeddings", 8192),
            DETAILED_CONTEXT_LENGTH,
        )

    def _build_prompt(self, chapter_text):
        messages = [
            {"role": "system", "content": DETAILED_SYSTEM_PROMPT},
            {"role": "user", "content": chapter_text},
        ]
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    def _text_chunks(self, text):
        placeholder = "x"
        full = self._build_prompt(placeholder)
        overhead = len(self.tokenizer.encode(full)) - len(
            self.tokenizer.encode(placeholder)
        )
        max_input = self.context_length - DETAILED_OUTPUT_RESERVE
        max_text = max_input - overhead

        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_text:
            return [text]

        chunks = []
        for i in range(0, len(tokens), max_text):
            chunk_tokens = tokens[i : i + max_text]
            chunks.append(
                self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            )
        return chunks

    def summarize_chapters(self, chapters):
        results = []
        for ch in tqdm(chapters, desc="Summarizing (detailed)"):
            chunk_summaries = []
            for chunk in self._text_chunks(ch["text"]):
                prompt = self._build_prompt(chunk)
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.context_length,
                ).to(self.device)

                attention_mask = inputs.get("attention_mask")
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=DETAILED_MAX_LENGTH,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                )

                summary = self.tokenizer.decode(
                    outputs[0][inputs.input_ids.shape[1] :],
                    skip_special_tokens=True,
                ).strip()
                chunk_summaries.append(summary)

            results.append(
                {"title": ch["title"], "summary": "\n\n".join(chunk_summaries)}
            )
        return results
