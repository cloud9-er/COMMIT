# STDLIB Log – PulseWire

## Why this exists

PulseWire was intentionally designed to minimize unnecessary dependencies by leveraging Python's standard library wherever possible. This improves portability, reduces installation overhead, increases reliability, and demonstrates a deeper understanding of Python's built-in capabilities.

---

## 1. `urllib.parse` instead of URL parsing libraries

**Package avoided:** furl / yarl

**Standard library used:** `urllib.parse`

**Where:** URL normalization and query parameter extraction.

**Why:** `urllib.parse` provides robust parsing, joining, encoding, and decoding of URLs without requiring an additional dependency.

---

## 2. `json` instead of `ujson`

**Package avoided:** ujson

**Standard library used:** `json`

**Where:** Exporting scraped data into JSON files and API responses.

**Why:** The built-in module is fully compliant with the JSON specification and is sufficient for PulseWire's workload.

---

## 3. `sqlite3` instead of a full ORM

**Package avoided:** SQLAlchemy

**Standard library used:** `sqlite3`

**Where:** Local storage of scraped pages, request metadata, and crawl history.

**Why:** PulseWire uses a lightweight relational database, making SQLite ideal without the complexity of an ORM.

---

## 4. `pathlib` instead of `pathlib2`

**Package avoided:** pathlib2

**Standard library used:** `pathlib`

**Where:** Managing export folders and cache directories.

**Why:** `pathlib` offers object-oriented, cross-platform file handling built directly into modern Python.

---

## 5. `collections.deque` instead of queue libraries

**Package avoided:** external queue implementations

**Standard library used:** `collections.deque`

**Where:** Breadth-first crawling queue.

**Why:** `deque` provides O(1) append and pop operations, making it perfect for high-performance crawl scheduling.

---

## 6. `hashlib` instead of checksum packages

**Package avoided:** xxhash / checksum utilities

**Standard library used:** `hashlib`

**Where:** Generating page fingerprints and duplicate detection.

**Why:** SHA-256 hashing reliably identifies identical content while remaining dependency-free.

---

## 7. `threading` instead of concurrency helpers

**Package avoided:** lightweight threading wrappers

**Standard library used:** `threading`

**Where:** Background monitoring and task coordination.

**Why:** Python already provides synchronization primitives such as Locks and Events without external libraries.

---

## 8. `time` instead of scheduling packages

**Package avoided:** schedule

**Standard library used:** `time`

**Where:** Request delays, retry intervals, and crawl timing.

**Why:** PulseWire only requires precise sleep intervals and timestamps, which the standard library already provides.

---

## 9. `csv` instead of dataframe libraries

**Package avoided:** pandas (for CSV export)

**Standard library used:** `csv`

**Where:** Exporting scraped results into spreadsheet-compatible CSV files.

**Why:** Structured row-by-row writing is efficient and avoids introducing a large dependency solely for exporting data.

---

## 10. `logging` instead of third-party logging frameworks

**Package avoided:** loguru

**Standard library used:** `logging`

**Where:** Request lifecycle, crawler status, retries, and error reporting.

**Why:** Python's logging module supports levels, formatting, file handlers, and structured debugging while remaining production-ready.

---

# Summary

| Standard Library | Replaced Purpose |
|------------------|------------------|
| `urllib.parse` | URL parsing |
| `json` | JSON serialization |
| `sqlite3` | Database storage |
| `pathlib` | File paths |
| `collections.deque` | Crawl queue |
| `hashlib` | Duplicate detection |
| `threading` | Background workers |
| `time` | Timing & retries |
| `csv` | CSV export |
| `logging` | Application logging |

## Impact

By prioritizing Python's standard library, PulseWire reduces dependency count, simplifies deployment, improves maintainability, and demonstrates efficient use of built-in language features without sacrificing functionality.
