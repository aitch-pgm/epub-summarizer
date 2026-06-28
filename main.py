import argparse
import sys

from epub_parser import extract_chapters
from summarizer import Summarizer, InstructSummarizer, DEFAULT_MODEL, DETAILED_MODEL
from output import write_summary, write_detailed_summary


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
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Generate an additional file with structured chapter summaries (Key Ideas, Golden Nuggets, etc.)",
    )
    parser.add_argument(
        "--detailed-model",
        default=DETAILED_MODEL,
        help=f"Model for detailed summaries (default: {DETAILED_MODEL})",
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

    if args.detailed:
        summaries = summarizer.summarize_chapters(chapters)
        output_path = args.output or f"{args.epub.rsplit('.', 1)[0]}_summary.txt"
        write_summary(info, summaries, args.model, output_path)
        print(f"Summary written to {output_path}")

        detailed_summarizer = InstructSummarizer(
            model_name=args.detailed_model, device=args.device
        )
        detailed = detailed_summarizer.summarize_chapters(chapters)
        detailed_path = f"{args.epub.rsplit('.', 1)[0]}_detailed.txt"
        write_detailed_summary(info, detailed, args.detailed_model, detailed_path)
        print(f"Detailed summary written to {detailed_path}")
    else:
        summaries = summarizer.summarize_chapters(chapters)
        output_path = args.output or f"{args.epub.rsplit('.', 1)[0]}_summary.txt"
        write_summary(info, summaries, args.model, output_path)
        print(f"Summary written to {output_path}")


if __name__ == "__main__":
    main()
