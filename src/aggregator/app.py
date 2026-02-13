import argparse
import os
from math import ceil
from flask import Flask, render_template, request, jsonify

from aggregator.store import search_iocs, get_filter_values, count_iocs, get_stats


def _get_int(value: str, default: int, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return default
    if parsed < minimum:
        parsed = minimum
    if maximum is not None and parsed > maximum:
        parsed = maximum
    return parsed


def create_app(db_path: str) -> Flask:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    templates_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")
    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)

    @app.route("/")
    def index():
        query = request.args.get("query", "")
        ioc_type = request.args.get("type", "")
        source = request.args.get("source", "")
        severity = request.args.get("severity", "")
        search_mode = request.args.get("search_mode", "simple")  # simple, regex, cidr
        date_from = request.args.get("date_from", "")
        date_to = request.args.get("date_to", "")
        page = _get_int(request.args.get("page", "1"), default=1, minimum=1)
        page_size = _get_int(request.args.get("page_size", "200"), default=200, minimum=1, maximum=1000)

        total_results = count_iocs(
            db_path,
            query=query,
            ioc_type=ioc_type,
            source=source,
            severity=severity,
            search_mode=search_mode,
            date_from=date_from,
            date_to=date_to,
        )
        page_count = max(ceil(total_results / page_size), 1) if total_results else 1
        page = min(page, page_count)
        offset = (page - 1) * page_size

        results = search_iocs(
            db_path,
            query=query,
            ioc_type=ioc_type,
            source=source,
            severity=severity,
            search_mode=search_mode,
            date_from=date_from,
            date_to=date_to,
            limit=page_size,
            offset=offset,
        )
        filters = get_filter_values(db_path)
        stats = get_stats(db_path)
        sources = filters["sources"]
        types = filters["types"]
        severities = filters["severities"]

        return render_template(
            "index.html",
            iocs=results,
            query=query,
            selected_type=ioc_type,
            selected_source=source,
            selected_severity=severity,
            search_mode=search_mode,
            date_from=date_from,
            date_to=date_to,
            sources=sources,
            types=types,
            severities=severities,
            page=page,
            page_size=page_size,
            page_count=page_count,
            total_results=total_results,
            stats=stats,
        )

    @app.route("/api/iocs", methods=["GET"])
    def api_search_iocs():
        """Search IOCs via REST API.
        
        Query Parameters:
        - query: Search term
        - type: IOC type filter
        - source: Source filter
        - severity: Severity filter
        - search_mode: simple|regex|cidr (default: simple)
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        - page: Page number (default: 1)
        - page_size: Results per page (default: 200, max: 1000)
        """
        try:
            query = request.args.get("query", "")
            ioc_type = request.args.get("type", "")
            source = request.args.get("source", "")
            severity = request.args.get("severity", "")
            search_mode = request.args.get("search_mode", "simple")
            date_from = request.args.get("date_from", "")
            date_to = request.args.get("date_to", "")
            page = _get_int(request.args.get("page", "1"), default=1, minimum=1)
            page_size = _get_int(request.args.get("page_size", "200"), default=200, minimum=1, maximum=1000)

            total_results = count_iocs(
                db_path,
                query=query,
                ioc_type=ioc_type,
                source=source,
                severity=severity,
                search_mode=search_mode,
                date_from=date_from,
                date_to=date_to,
            )
            page_count = max(ceil(total_results / page_size), 1) if total_results else 1
            page = min(page, page_count)
            offset = (page - 1) * page_size

            results = search_iocs(
                db_path,
                query=query,
                ioc_type=ioc_type,
                source=source,
                severity=severity,
                search_mode=search_mode,
                date_from=date_from,
                date_to=date_to,
                limit=page_size,
                offset=offset,
            )

            return jsonify({
                "status": "success",
                "data": results,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_pages": page_count,
                    "total_results": total_results,
                }
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/api/stats", methods=["GET"])
    def api_stats():
        """Get aggregation statistics."""
        try:
            stats = get_stats(db_path)
            return jsonify({
                "status": "success",
                "data": stats
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/api/filters", methods=["GET"])
    def api_filters():
        """Get available filter values."""
        try:
            filters = get_filter_values(db_path)
            return jsonify({
                "status": "success",
                "data": filters
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/api/health", methods=["GET"])
    def api_health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "Threat Feed Aggregator",
            "version": "1.0.0"
        })

    return app


def run() -> None:
    parser = argparse.ArgumentParser(description="Threat feed dashboard")
    parser.add_argument("--db", default="data/iocs.db", help="Path to IOC SQLite DB")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    app = create_app(args.db)
    app.run(host=args.host, port=args.port, debug=False)
