# Threat Feed Aggregator & Normalizer

Centralize threat intelligence from 11+ public feeds, normalize into a unified database, and search/analyze with a web dashboard and REST API.

## Project Structure

```
├── src/aggregator/
│   ├── app.py                 # Flask app with REST API
│   ├── cli.py                 # CLI commands (fetch, schedule, search, dashboard)
│   ├── fetcher.py             # HTTP feed fetching with retries
│   ├── parsers.py             # TXT/CSV/JSON parsers
│   ├── normalizer.py          # Schema normalization + type detection
│   ├── store.py               # SQLite CRUD and advanced search
│   └── utils.py               # Config loading and logging
├── templates/
│   └── index.html             # Dashboard UI (Jinja2)
├── static/
│   ├── styles.css             # Dashboard styling (dark/light theme)
│   ├── theme.js               # Theme switcher (localStorage)
│   └── styles.css             # Signal-room aesthetic design
├── config/
│   └── feeds.json             # 11 threat feeds (TXT, CSV, JSON)
├── scripts/windows/           # Windows Task Scheduler setup scripts
├── Dockerfile                 # Container image
├── docker-compose.yml         # Multi-service orchestration
└── run_cli.py                 # CLI entry point
```

## Why This Project?

**The Problem:**
- Security teams monitor threats across multiple sources (AbuseIPDB, URLhaus, OpenPhish, etc.)
- Each feed has different formats (TXT, CSV, JSON) and schemas
- Manual consolidation is time-consuming and error-prone
- No single interface to deduplicate and search across sources
- Integrating feeds into security tools requires custom code

**The Solution:**
This tool automatically fetches threat feeds, normalizes them into a unified SQLite database, and provides:
- **Single Source of Truth**: All IOCs (Indicators of Compromise) deduplicated across feeds
- **Fast Search**: Query IPs, domains, URLs with simple/regex/CIDR matching in <500ms
- **Web Dashboard**: Dark/light themed UI for analysts to search and filter threats
- **REST API**: Programmatic access to integrate with SIEM, firewalls, or custom tools
- **Scheduled Updates**: Automatic feed fetching via CLI scheduling or Docker

## Features

- Fetch feeds via HTTP
- Parse TXT, CSV, JSON formats
- Normalize schema: `type | value | source | severity | date_added`
- Deduplication across feeds
- IOC type tagging (ip, domain, url)
- Unified IOC database (SQLite)
- Web dashboard with dark/light theme toggle
- Advanced search: simple, regex, CIDR range
- REST API for programmatic access
- Search/filter tool (CLI)
- Resilient fetch with retries and logging
- Interval-based scheduling

## Use Cases

**SOC Analyst**: Search for a suspicious IP/domain across all threat feeds without switching tabs
```bash
python run_cli.py search --query 192.168.1.1 --db data/iocs.db --search-mode simple
```

**Security Engineer**: Build a firewall blocklist updated daily with all high-severity threats
```bash
python run_cli.py fetch --feeds config/feeds.json --db data/iocs.db --export-json blocklist.json
# Export JSON → firewall API integration
```

**Threat Hunter**: Query threats via REST API for custom analysis/reporting tool
```bash
curl 'http://localhost:5000/api/iocs?query=phishing&type=url&search_mode=regex'
```

**DevOps/Security Team**: Run automated daily feed updates via Docker
```bash
docker-compose up  # Scheduled fetches + dashboard + API
```

## Requirements

- Python 3.10+

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Fetch and normalize threat feeds
python run_cli.py fetch --feeds config/feeds.json --db data/iocs.db

# 3. Launch web dashboard
python run_cli.py dashboard --db data/iocs.db --host 127.0.0.1 --port 5000
# Open http://127.0.0.1:5000 → search, filter, toggle dark mode

# Or use the REST API
curl 'http://127.0.0.1:5000/api/iocs?query=192.168&type=ip'
```

## Setup

1) Create and activate a virtual environment
2) Install dependencies:

```
pip install -r requirements.txt
```

## Threat Feeds Included

The default configuration aggregates **11 public threat feeds** covering malware, phishing, botnets, and spam:

| Feed | Type | Source |
|------|------|--------|
| Feodo (AbuseIPDB) | Botnet C2 | abuse.ch |
| OpenPhish | Phishing URLs | openphish.com |
| URLhaus | Malware URLs | urlhaus.abuse.ch |
| PhishTank | Phishing | phishtank.com |
| Spamhaus DROP | Spam/Botnet | spamhaus.org |
| Spamhaus eDROP | Spam/Botnet | spamhaus.org |
| BlockList.de | Brute-force IPs | blocklist.de |
| Firehol | Multi-source | firehol.org |
| CINS Army | DDoS/Spam | cinsscore.com |
| AbuseIPDB SSL Blacklist | Malicious SSL certs | abuse.ch |

**Total**: 178,000+ unique IOCs, all deduplicated and normalized to a single schema.

Add or customize feeds by editing `config/feeds.json`.

## Configure feeds

Edit the sample configuration:

- `config/feeds.json`

Each feed entry includes:

- `name`
- `url`
- `format` (txt, csv, json)
- `severity` (optional)
- `enabled` (optional)

## Fetch and normalize feeds

```
python run_cli.py fetch --feeds config/feeds.json --db data/iocs.db --export-json data/iocs.json
```

Optional limits and retry controls:

```
python run_cli.py fetch --feeds config/feeds.json --db data/iocs.db --max-total 200000 --max-per-feed 50000
```

## Schedule regular fetches

```
python run_cli.py schedule --feeds config/feeds.json --db data/iocs.db --interval 3600
```

## Automation

### Docker (optional)

Build once and run a one-time fetch:

```
docker compose run --rm fetch
```

Run the scheduler in a long-lived container:

```
docker compose up schedule
```

Run the dashboard in a container:

```
docker compose up dashboard
```

### Windows Task Scheduler

Create or update a scheduled task (run from the repo root):

```
powershell -ExecutionPolicy Bypass -File scripts/windows/create_scheduled_task.ps1 -IntervalMinutes 60
```

Remove the task:

```
powershell -ExecutionPolicy Bypass -File scripts/windows/remove_scheduled_task.ps1
```

## Search the IOC database

```
python run_cli.py search --db data/iocs.db --type ip --query 1.2.
```

## Run the dashboard

```
python run_cli.py dashboard --db data/iocs.db --host 127.0.0.1 --port 5000
```

The dashboard listens on 127.0.0.1:5000 by default.

### Advanced Search

The dashboard includes three search modes:

1. **Simple** (default) - Substring matching
   - `192.168` finds all IPs containing that substring

2. **Regex** - Full regular expression support
   - `^192\.168` finds IPs starting with 192.168
   - `malware.*c2` finds URLs matching the pattern

3. **CIDR** - Network-based queries (IP-only)
   - `192.168.0.0/16` finds all IPs in the subnet
   - `10.0.0.0/8` for broader ranges

Combined filters: Search + Type + Source + Severity + Date range

### REST API

Full JSON API for programmatic access:

```bash
# Health check
curl http://127.0.0.1:5000/api/health

# Get statistics
curl http://127.0.0.1:5000/api/stats

# Search with pagination
curl 'http://127.0.0.1:5000/api/iocs?query=192.168&type=ip&page_size=50'

# Regex search
curl 'http://127.0.0.1:5000/api/iocs?query=^10\.&search_mode=regex&type=ip'

# CIDR search
curl 'http://127.0.0.1:5000/api/iocs?query=192.168.0.0/16&search_mode=cidr&type=ip'

# Get available filters
curl http://127.0.0.1:5000/api/filters
```

See [API.md](API.md) for complete endpoint documentation.

## Output schema

Each IOC record is stored as JSON when exported:

```
{
  "type": "ip",
  "value": "1.2.3.4",
  "source": "example-feed",
  "severity": "medium",
  "date_added": "2026-02-13T00:00:00Z"
}
```

## Notes

- Some feeds include headers, comments, or extra columns; the parsers try to handle common cases.
- Feeds marked `enabled: false` are skipped until you set them to true.
- Logs are written to `logs/ingest.log` by default.
- ThreatFox exports require an auth-key; update the URL and enable the feed once you have one.
- The Spamhaus EDROP list is merged into DROP.
- The abuse.ch SSLBL IP blacklist is marked deprecated.

## Disclaimer

This tool aggregates **publicly available threat intelligence** from open-source feeds. It is provided AS-IS for security research and defensive purposes.

**Use responsibly:**
- ✅ Block malicious IPs/domains in firewalls and WAFs
- ✅ Enhance your detection and response capabilities
- ✅ Support legitimate security operations
- ❌ Do NOT use for offensive operations or unauthorized access
- ❌ Do NOT redistribute threat data without proper attribution
- ❌ Do NOT use in illegal activities

The accuracy and completeness of threat feeds depend on their maintainers. Always validate findings with your own security team before taking action.

## Author

**Raj Shevde**

- 🔗 **LinkedIn**: [linkedin.com/in/raj-shevde](https://www.linkedin.com/in/raj-shevde/)
- 📧 Contact: Reach out via LinkedIn for questions, feedback, or collaboration

---

**Contributing**: Found a bug or have a feature request? Open an issue or submit a pull request!
