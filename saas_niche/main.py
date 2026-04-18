"""Command-line entry point for SaasNiche."""

import argparse
import sys
from pathlib import Path
from typing import Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _run_crawler(test_mode: bool = False) -> None:
    from saas_niche.crawler.reddit_crawler import run

    run(test_mode=test_mode)


def _run_classifier() -> None:
    from saas_niche.classifier.classifier import run

    run()


def _run_scorer() -> None:
    from saas_niche.scorer.scorer import run

    run()


def _run_clusterer() -> None:
    from saas_niche.embeddings.clusterer import run

    run()


def _run_blueprint() -> None:
    from saas_niche.blueprints.blueprint_gen import run

    run()


def _run_pipeline() -> None:
    from saas_niche.pipeline.runner import run

    run()


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(prog="saas_niche")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl")
    crawl_parser.add_argument(
        "--test",
        action="store_true",
        help="Run the crawler against 3 subreddits and 1 sort only.",
    )

    command_map: dict[str, Callable[[], None]] = {
        "classify": _run_classifier,
        "score": _run_scorer,
        "cluster": _run_clusterer,
        "blueprint": _run_blueprint,
        "run": _run_pipeline,
    }

    for name, handler in command_map.items():
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(handler=handler)

    return parser


def main() -> None:
    """Execute the selected CLI subcommand."""

    parser = build_parser()
    args = parser.parse_args()
    if args.command == "crawl":
        _run_crawler(test_mode=args.test)
        return
    args.handler()


if __name__ == "__main__":
    main()
