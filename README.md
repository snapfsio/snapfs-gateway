# SnapFS Gateway

The SnapFS Gateway is the central HTTP and WebSocket API layer for SnapFS.
It acts as the front door to the system and abstracts all internal storage and
event infrastructure.

All SnapFS clients - scanners, agents, CLIs, dashboards - talk only to the Gateway,
never directly to databases or NATS.

## Features

#### L1 Cache Probe API — /cache/batch

- Fast hash lookups using the Redis L1 cache.
- Scanners use this to avoid re-hashing unchanged files.

#### Ingest API — /ingest

- Accepts file events (file.upsert, etc.) from scanners:
- Seeds Redis L1 cache
- Publishes events into NATS JetStream for downstream agents

#### WebSocket Event Stream — /stream

- Agents (MySQL, Elasticsearch, analytics, etc.) connect via WS:

```
ws://gateway/stream?subject=snapfs.files&durable=mysql&batch=100
```

The Gateway:

- Reads from JetStream using a durable consumer
- Streams batches of events to agents
- Waits for ACKs over WebSocket
- ACKs JetStream messages on agent acknowledgement

This makes agents plug-and-play with zero knowledge of NATS.

## Query API — /query/sql

Gateway-provided SQL querying (direct MySQL integration for now).
Later this may be handled by a dedicated query agent.

## Architecture Overview

```
Scanner → HTTP /ingest ─────┐
                            │
                         JetStream (durable event log)
                            │
          Redis (L1)  ←─── Gateway ───→ /cache/batch
                            │
                    WS /stream to agents
                            │
            ┌───────────────┴────────────────┐
            ▼               ▼                ▼
       MySQL Agent      ES Agent        Other Agents
```

## Responsibilities

| Component                 | Purpose                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| **Gateway**               | HTTP interface, Redis L1, WS streaming, NATS JetStream abstraction |
| **Scanner (snapfs scan)** | Hash files, send `file.upsert` to Gateway                          |
| **Agents**                | Consume events via WebSocket, write to backend (MySQL, ES, etc.)   |
| **Redis**                 | L1 hot cache for hash lookups                                      |
| **NATS JetStream**        | Durable event log & consumer management                            |

## Status

Early development. APIs and schemas are still evolving.

## License

Apache 2.0. See `LICENSE` for details.
