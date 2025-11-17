# SnapFS Gateway

The SnapFS Gateway is the HTTP/JSON API layer for SnapFS. It sits in front of
the underlying storage backends (e.g. MySQL, Elasticsearch) and exposes:

- Cache probe API (`/cache/batch`)
- Ingest API for file events (`/ingest`)
- Query API for metadata and file search (`/query/sql`, etc.)

All SnapFS clients (CLI, agents, scanners) talk to the gateway – not directly
to the database.

## Status

Early development. APIs and schemas are still evolving.

## License

Apache 2.0. See `LICENSE` for details.
