# REST API Documentation

The Threat Feed Aggregator includes a comprehensive REST API for programmatic access to IOC data.

## Base URL

```
http://127.0.0.1:5000/api
```

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check if the API service is operational.

**Response:**
```json
{
  "status": "healthy",
  "service": "Threat Feed Aggregator",
  "version": "1.0.0"
}
```

**Example:**
```bash
curl http://127.0.0.1:5000/api/health
```

---

### 2. Search IOCs

**GET** `/api/iocs`

Search for Indicators of Compromise with advanced filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | "" | Search term |
| `search_mode` | string | "simple" | Search mode: `simple`, `regex`, or `cidr` |
| `type` | string | "" | Filter by IOC type (ip, url, domain) |
| `source` | string | "" | Filter by feed source |
| `severity` | string | "" | Filter by severity (high, medium, low) |
| `date_from` | string | "" | Start date (YYYY-MM-DD) |
| `date_to` | string | "" | End date (YYYY-MM-DD) |
| `page` | integer | 1 | Page number for pagination |
| `page_size` | integer | 200 | Results per page (max 1000) |

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "ip",
      "value": "192.168.1.1",
      "source": "firehol",
      "severity": "high",
      "date_added": "2024-02-13T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 200,
    "total_pages": 5,
    "total_results": 1087
  }
}
```

**Examples:**

Simple substring search:
```bash
curl 'http://127.0.0.1:5000/api/iocs?query=192&type=ip'
```

Regex pattern search (find IPs starting with 192.168):
```bash
curl 'http://127.0.0.1:5000/api/iocs?query=^192\.168&search_mode=regex&type=ip'
```

CIDR range search (find IPs in subnet):
```bash
curl 'http://127.0.0.1:5000/api/iocs?query=192.168.0.0/16&search_mode=cidr&type=ip'
```

Filter by source and severity:
```bash
curl 'http://127.0.0.1:5000/api/iocs?source=urlhaus&severity=high&page_size=50'
```

Date range filter:
```bash
curl 'http://127.0.0.1:5000/api/iocs?date_from=2024-01-01&date_to=2024-02-13'
```

Pagination:
```bash
curl 'http://127.0.0.1:5000/api/iocs?page=2&page_size=100'
```

---

### 3. Get Statistics

**GET** `/api/stats`

Retrieve aggregation statistics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_iocs": 178821,
    "total_records": 179511,
    "total_sources": 10,
    "last_updated": "2024-02-13T14:25:30Z",
    "by_type": {
      "ip": 45413,
      "url": 133408
    }
  }
}
```

**Example:**
```bash
curl http://127.0.0.1:5000/api/stats
```

---

### 4. Get Available Filters

**GET** `/api/filters`

Retrieve available filter options for search.

**Response:**
```json
{
  "status": "success",
  "data": {
    "types": ["ip", "url"],
    "sources": [
      "abusech-feodo",
      "emergingthreats",
      "openphish",
      "firehol",
      "urlhaus",
      "blocklistde",
      "phishtank",
      "spamhaus-drop",
      "spamhaus-edrop",
      "cins-army",
      "abusech-sslbl"
    ],
    "severities": ["high", "medium"]
  }
}
```

**Example:**
```bash
curl http://127.0.0.1:5000/api/filters
```

---

## Search Modes

### Simple (Default)
Substring matching - finds partial matches in IOC values.

```bash
# Find IPs containing "192.168"
curl 'http://127.0.0.1:5000/api/iocs?query=192.168&type=ip&search_mode=simple'
```

### Regex Pattern
Full regular expression support for powerful pattern matching.

```bash
# Find URLs containing "phishing" or "malware"
curl 'http://127.0.0.1:5000/api/iocs?query=(phishing|malware)&search_mode=regex&type=url'

# Find IP addresses starting with 10.
curl 'http://127.0.0.1:5000/api/iocs?query=^10\.&search_mode=regex&type=ip'
```

### CIDR Range (IP-only)
Network-based queries to find all IPs within a subnet.

```bash
# Find all IPs in the 192.168.0.0/16 subnet
curl 'http://127.0.0.1:5000/api/iocs?query=192.168.0.0/16&search_mode=cidr&type=ip'

# Support for IPv6
curl 'http://127.0.0.1:5000/api/iocs?query=2001:db8::/32&search_mode=cidr&type=ip'
```

---

## Error Handling

All API endpoints return appropriate HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid parameters or query
- **404 Not Found**: Endpoint does not exist
- **500 Internal Server Error**: Server error

**Error Response:**
```json
{
  "status": "error",
  "message": "Invalid regex pattern: unterminated character set"
}
```

---

## Usage Examples

### Python

```python
import requests

BASE_URL = "http://127.0.0.1:5000/api"

# Get stats
resp = requests.get(f"{BASE_URL}/stats")
print(resp.json())

# Search IOCs
resp = requests.get(f"{BASE_URL}/iocs", params={
    "query": "192.168",
    "type": "ip",
    "search_mode": "simple",
    "page_size": 50
})
results = resp.json()
print(f"Found {results['pagination']['total_results']} matches")
```

### JavaScript

```javascript
const BASE_URL = 'http://127.0.0.1:5000/api';

// Get filters
fetch(`${BASE_URL}/filters`)
  .then(r => r.json())
  .then(data => console.log(data.data.types));

// Search with parameters
const params = new URLSearchParams({
  query: '^192\\.168',
  search_mode: 'regex',
  type: 'ip'
});

fetch(`${BASE_URL}/iocs?${params}`)
  .then(r => r.json())
  .then(data => {
    console.log(`Found ${data.pagination.total_results} IPs`);
    data.data.forEach(ioc => console.log(ioc.value));
  });
```

### cURL

```bash
# Health check
curl http://127.0.0.1:5000/api/health

# Get stats
curl http://127.0.0.1:5000/api/stats | jq

# Complex search with jq parsing
curl -s 'http://127.0.0.1:5000/api/iocs?query=malware&type=url&severity=high' \
  | jq '.data[] | .value'

# Export to file
curl 'http://127.0.0.1:5000/api/iocs?page_size=1000' | jq '.data' > iocs.json
```

---

## Rate Limiting

Currently, no rate limiting is enforced. For production deployments, consider implementing rate limiting middleware.

---

## Pagination

Use `page` and `page_size` parameters to paginate through large result sets.

```bash
# Get page 1 with 100 results
curl 'http://127.0.0.1:5000/api/iocs?page=1&page_size=100'

# Get page 2
curl 'http://127.0.0.1:5000/api/iocs?page=2&page_size=100'
```

The response includes pagination metadata:
```json
{
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total_pages": 1795,
    "total_results": 179500
  }
}
```

---

## Filtering Combinations

All filters can be combined for precise queries:

```bash
# Find high-severity URLs from URLhaus added in the last 30 days
curl 'http://127.0.0.1:5000/api/iocs' \
  --data-urlencode 'type=url' \
  --data-urlencode 'source=urlhaus' \
  --data-urlencode 'severity=high' \
  --data-urlencode 'date_from=2024-01-14' \
  --data-urlencode 'date_to=2024-02-13'
```

---

## Data Fields

Each IOC record contains:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | IOC type: `ip`, `url`, or `domain` |
| `value` | string | The actual IOC value |
| `source` | string | Feed name it came from |
| `severity` | string | `high` or `medium` |
| `date_added` | string | ISO timestamp when added (Z = UTC) |

