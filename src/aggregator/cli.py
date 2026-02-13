import argparse
import json
import sys
import time

from aggregator.fetcher import fetch_feed
from aggregator.parsers import parse_feed
from aggregator.normalizer import normalize_items
from aggregator.store import upsert_iocs, search_iocs, export_iocs
from aggregator.utils import load_feeds_config, configure_logging
from aggregator.app import create_app


def _fetch_once(args: argparse.Namespace) -> tuple[int, int]:
    feeds = load_feeds_config(args.feeds)
    logger = configure_logging(args.log)
    all_iocs = []
    max_total = args.max_total if args.max_total is not None else 0

    logger.info("starting fetch feeds=%d", len(feeds))
    for feed in feeds:
        name = feed["name"]
        url = feed["url"]
        feed_format = feed["format"]
        severity = feed.get("severity")
        headers = feed.get("headers")

        try:
            raw_text = fetch_feed(
                url,
                headers=headers,
                timeout=args.timeout,
                retries=args.retries,
                backoff=args.backoff,
            )
        except Exception as exc:
            logger.warning("fetch failed name=%s error=%s", name, exc)
            continue

        items = list(parse_feed(raw_text, feed_format))
        iocs = normalize_items(items, source=name, default_severity=severity)

        if args.max_per_feed and len(iocs) > args.max_per_feed:
            iocs = iocs[: args.max_per_feed]

        if max_total:
            remaining = max_total - len(all_iocs)
            if remaining <= 0:
                logger.info("max total reached, stopping ingest")
                break
            if len(iocs) > remaining:
                iocs = iocs[:remaining]

        all_iocs.extend(iocs)
        logger.info("feed=%s items=%d iocs=%d", name, len(items), len(iocs))

    inserted = upsert_iocs(args.db, all_iocs)
    if args.export_json:
        export_iocs(args.db, args.export_json)
        logger.info("exported json path=%s", args.export_json)
    logger.info("run summary total=%d inserted=%d", len(all_iocs), inserted)
    return inserted, len(all_iocs)


def cmd_fetch(args: argparse.Namespace) -> int:
    inserted, total = _fetch_once(args)
    print(f"Inserted {inserted} IOC source records into {args.db}")
    print(f"Processed {total} normalized IOCs")
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    logger = configure_logging(args.log)
    iteration = 0
    while True:
        iteration += 1
        logger.info("schedule tick=%d", iteration)
        _fetch_once(args)
        if args.iterations and iteration >= args.iterations:
            logger.info("schedule complete iterations=%d", iteration)
            break
        time.sleep(args.interval)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    results = search_iocs(
        args.db,
        query=args.query,
        ioc_type=args.type,
        source=args.source,
        severity=args.severity,
        limit=args.limit,
    )
    json.dump(results, sys.stdout, indent=2)
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Run the Flask dashboard server."""
    app = create_app(args.db)
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0
    print("")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Threat feed aggregator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch and normalize feeds")
    fetch_parser.add_argument("--feeds", required=True, help="Path to feeds.json")
    fetch_parser.add_argument("--db", required=True, help="Path to SQLite DB")
    fetch_parser.add_argument("--export-json", default="", help="Optional JSON export path")
    fetch_parser.add_argument("--max-total", type=int, default=200000, help="Cap total IOCs per run")
    fetch_parser.add_argument("--max-per-feed", type=int, default=0, help="Cap IOCs per feed (0 = no cap)")
    fetch_parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    fetch_parser.add_argument("--retries", type=int, default=3, help="HTTP retries")
    fetch_parser.add_argument("--backoff", type=float, default=0.5, help="Retry backoff factor")
    fetch_parser.add_argument("--log", default="logs/ingest.log", help="Log file path")
    fetch_parser.set_defaults(func=cmd_fetch)

    schedule_parser = subparsers.add_parser("schedule", help="Fetch feeds on an interval")
    schedule_parser.add_argument("--feeds", required=True, help="Path to feeds.json")
    schedule_parser.add_argument("--db", required=True, help="Path to SQLite DB")
    schedule_parser.add_argument("--export-json", default="", help="Optional JSON export path")
    schedule_parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds")
    schedule_parser.add_argument("--iterations", type=int, default=0, help="0 = run forever")
    schedule_parser.add_argument("--max-total", type=int, default=200000, help="Cap total IOCs per run")
    schedule_parser.add_argument("--max-per-feed", type=int, default=0, help="Cap IOCs per feed (0 = no cap)")
    schedule_parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    schedule_parser.add_argument("--retries", type=int, default=3, help="HTTP retries")
    schedule_parser.add_argument("--backoff", type=float, default=0.5, help="Retry backoff factor")
    schedule_parser.add_argument("--log", default="logs/ingest.log", help="Log file path")
    schedule_parser.set_defaults(func=cmd_schedule)

    search_parser = subparsers.add_parser("search", help="Search IOC database")
    search_parser.add_argument("--db", required=True, help="Path to SQLite DB")
    search_parser.add_argument("--query", default="", help="Substring search on value")
    search_parser.add_argument("--type", dest="type", default="", help="Filter by IOC type")
    search_parser.add_argument("--source", default="", help="Filter by source")
    search_parser.add_argument("--severity", default="", help="Filter by severity")
    search_parser.add_argument("--limit", type=int, default=200, help="Max results")
    search_parser.set_defaults(func=cmd_search)

    dashboard_parser = subparsers.add_parser("dashboard", help="Run Flask dashboard with REST API")
    dashboard_parser.add_argument("--db", required=True, help="Path to SQLite DB")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="Server host")
    dashboard_parser.add_argument("--port", type=int, default=5000, help="Server port")
    dashboard_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    dashboard_parser.set_defaults(func=cmd_dashboard)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))
