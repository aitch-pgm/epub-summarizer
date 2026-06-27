import argparse
import sys

from epub_parser import extract_chapters
from summarizer import Summarizer, DEFAULT_MODEL
from output import write_summary


def main():
    parser = argparse.ArgumentParser(
        description="Summarize an EPUB book chapter by chapter using a local Hugging Face model."
    )
    parser.add_argument("epub", help="Path to the .epub file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: <epub_basename>_summary.txt)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Summarization model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "mps"],
        help="Override device auto-detection",
    )
    parser.add_argument(
        "--max-chapters",
        type=int,
        help="Only summarize the first N chapters (useful for testing)",
    )

    args = parser.parse_args()

    if not args.epub.endswith(".epub"):
        print("Error: input file must have a .epub extension", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {args.epub} ...")
    info = extract_chapters(args.epub)
    print(f"  Title:    {info['title']}")
    print(f"  Author:   {info['author']}")
    print(f"  Chapters: {len(info['chapters'])}")

    chapters = info["chapters"]
    if args.max_chapters:
        chapters = chapters[: args.max_chapters]
        print(f"  (limiting to first {args.max_chapters} chapter(s))")

    summarizer = Summarizer(model_name=args.model, device=args.device)
    summaries = summarizer.summarize_chapters(chapters)

    output_path = args.output or f"{args.epub.rsplit('.', 1)[0]}_summary.txt"
    write_summary(info, summaries, args.model, output_path)
    print(f"\nSummary written to {output_path}")


if __name__ == "__main__":
    main()
