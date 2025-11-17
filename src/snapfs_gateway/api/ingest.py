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
    subject: Optional[str] = Query(None, description="Optional subject for routing"),
):
    """
    Ingest a list of events.

    The SnapFS scanner sends file.upsert events here. For now this stub
    just acknowledges them; later it will forward to snapfs-agent-mysql,
    NATS, or other backends.
    """
    # TODO: forward events to snapfs-agent-mysql (or NATS stream)
    # e.g. ingest.apply_events(subject, body.events)
    return IngestResponse(status="ok", received=len(body.events), subject=subject)
