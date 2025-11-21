#!/usr/bin/env python3
#
# Copyright (c) 2025 SnapFS, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..bus import bus
from ..cache_keys import build_cache_key
from ..config import settings

router = APIRouter(tags=["ingest"])


class Event(BaseModel):
    type: str
    data: Dict[str, Any]


class IngestRequest(BaseModel):
    events: List[Event]


class IngestResponse(BaseModel):
    status: str
    received: int
    subject: Optional[str] = None


@router.post("/ingest", response_model=IngestResponse)
async def ingest_events(
    body: IngestRequest,
    subject: Optional[str] = Query(
        None,
        description="Optional subject for routing; defaults to SNAPFS_SUBJECT.",
    ),
):
    """
    Ingest a list of events from scanners/clients.

    For now we:
    - Seed Redis L1 cache for file.upsert events that include algo + hash
    - Publish the entire event list to JetStream for downstream agents
    """
    subj = subject or settings.default_subject
    received = len(body.events)

    # 1) Seed Redis (L1 cache) for file.upsert events
    for ev in body.events:
        if ev.type != "file.upsert":
            continue

        data = ev.data or {}
        algo = data.get("algo")
        hash_hex = data.get("hash")
        path = data.get("path")
        size = data.get("size")
        mtime = data.get("mtime")

        if not (
            algo
            and hash_hex
            and path is not None
            and size is not None
            and mtime is not None
        ):
            continue

        key = build_cache_key(
            path=path,
            size=int(size),
            mtime=float(mtime),
            inode=data.get("inode"),
            dev=data.get("dev"),
        )
        await bus.cache_set(
            key,
            {
                "algo": algo,
                "hash": hash_hex,
            },
            ttl=3600,
        )

    # 2) Publish to JetStream as a single message with all events for agents
    await bus.publish_events(
        subject=subj,
        events=[e.dict() for e in body.events],
    )

    return IngestResponse(status="ok", received=received, subject=subj)
